"""Export the slim MK1 frame, retainer and assembly in millimetres."""

from argparse import ArgumentParser
from itertools import combinations
import json
from pathlib import Path

import cadquery as cq

from slim_frame import (
    SlimFrameParams, build_foam_reference, build_glass_references,
    build_slim_frame, build_snap_coupon, place_at_lens,
    cut_templates, design_metadata,
)
from slim_channel import CrownChannel, channel_frame
from slim_harness import WIRE_OD, build_harness, plug_backs
from slim_mount import (
    TEMPLE_CLEARANCE_PER_SIDE, MountParams, design_data, mount_coupon,
    make_keepouts, make_shell, fit_pcb_mount,
    make_references, make_strap_references, pcb_location, strap_coupon,
)


HERE = Path(__file__).resolve().parent
COLORS = {
    "shell": (0.09, 0.09, 0.10),
    "retainer": (0.10, 0.10, 0.11),
    "glass": (0.28, 0.43, 0.40),
    "terminal": (0.54, 0.49, 0.34),
    "pcb": (0.13, 0.23, 0.20),
    "battery": (0.58, 0.60, 0.67),
    "liner": (0.08, 0.10, 0.11),
    "elastic": (0.04, 0.05, 0.05),
    "left_lead": (.95, .42, .05),
    "right_lead": (.12, .65, .82),
    "pack_lead": (.58, .24, .35),
    "plug": (.83, .82, .76),
    "brass": (.64, .46, .21),
    "hardware": (0.12, 0.12, 0.12),
}


def as_shape(part):
    if isinstance(part, cq.Shape):
        return part
    solids = part.solids().vals()
    return solids[0] if len(solids) == 1 else cq.Compound.makeCompound(solids)


def overlap(a, b):
    ab, bb = a.BoundingBox(), b.BoundingBox()
    for axis in "xyz":
        if min(getattr(ab, axis + "max"), getattr(bb, axis + "max")) <= max(
            getattr(ab, axis + "min"), getattr(bb, axis + "min")
        ) + 1e-5:
            return 0.0
    return sum(s.Volume(tol=1e-6) for s in a.intersect(b).Solids())


def material(name):
    if name == "shared_retainer":
        return "retainer"
    if name.startswith("lcd_"):
        return "glass"
    if name.startswith("terminal_"):
        return "terminal"
    if "foam" in name:
        return "liner"
    if "elastic" in name:
        return "elastic"
    if name.startswith("wire_") or name.startswith("jumper_"):
        return "left_lead" if "left" in name else "right_lead" if "right" in name else "pack_lead"
    if name.startswith("plug_"):
        return "plug"
    if name.startswith("insert_"):
        return "brass"
    if name.startswith("pcb_screw"):
        return "hardware"
    if name in COLORS:
        return name
    return "shell"


def on_print_bed(shape, angle):
    rotated = shape.rotate((0, 0, 0), (1, 0, 0), angle)
    b = rotated.BoundingBox()
    return rotated.translate((-(b.xmin + b.xmax) / 2,
                              -(b.ymin + b.ymax) / 2, -b.zmin))


def export_mesh(shape, path):
    if not shape.exportStl(str(path), tolerance=0.02, angularTolerance=0.08, relative=False):
        raise RuntimeError(f"Could not export {path}")


def export_lens_coupon(frame, retainer, p, output):
    """One complete pocket and latch for trying a pair of actual wired shutters."""
    inside_x = p.pd / 2 - p.glass_w / 2 - 6
    width = p.glass_w + 16
    crop = (cq.Workplane("XY").box(width, 38, 52, centered=(False, False, True))
            .translate((inside_x, -17, 0)).val())
    folder = output / "lens-test"
    folder.mkdir(exist_ok=True)
    for name, part, angle in (("lens_bay", frame, 0), ("lens_retainer", retainer, 90)):
        sample = part.intersect(crop)
        if not sample.isValid() or len(sample.Solids()) != 1:
            raise ValueError(f"Invalid {name} fit coupon")
        export_mesh(on_print_bed(sample, angle), folder / f"{name}.stl")


def emboss_wordmark(frame, p):
    """Raise the letters on the outward face of the right lens rim."""
    # The front of this bay is planar. The side of the bridge rolls away
    # quickly enough to obscure lettering when viewed at a shallow angle.
    top = p.front_y + .30
    plane = cq.Plane(origin=(p.pd / 2, top, 18.6), xDir=(-1, 0, 0), normal=(0, 1, 0))
    letters = cq.Workplane(plane).text("rivercraft", 5.0, -1.0, font="Arial",
                                      kind="bold", combine=False).solids().vals()
    # The full footprint of every stroke must seat on the rim, including the
    # dot on the i. The check uses the same glyph outlines as the final STL.
    root_plane = cq.Workplane(plane).workplane(offset=-.95).rect(35, 7).extrude(.05).val()
    for letter in letters:
        root = place_at_lens(letter.intersect(root_plane), p)
        if not root.Solids() or root.cut(frame).Volume() > 1e-5:
            raise ValueError("Wordmark extends beyond the brow face")
    return frame.fuse(*[place_at_lens(letter, p) for letter in letters]).clean()


def board_fasteners(mount):
    """M2x4 screws and 0.3 mm washers fitted to the actual PCB notches."""
    hardware = {}
    axis = cq.Vector(1, 0, 0)
    p = MountParams(**mount["parameters"])
    for index, site in enumerate(mount["pcb_screws"], 1):
        x, y, z = site["position"]
        washer_origin = cq.Vector(x + 1, y, z)
        washer = cq.Solid.makeCylinder(2.5, .3, washer_origin, axis).cut(
            cq.Solid.makeCylinder(1.1, .3, washer_origin, axis)
        )
        head_origin = cq.Vector(x + 1.3, y, z)
        head_radius, head_height = (1.675, 1.60) if p.insert_diameter is None else (1.75, 1.30)
        head = cq.Solid.makeCylinder(head_radius, head_height, head_origin, axis)
        # Threads form during installation. Show the engaged section by a core
        # inside the pilot, and the full screw diameter through board and washer.
        if p.insert_diameter is None:
            core = cq.Solid.makeCylinder(.77, 2.7, head_origin - axis * 4, axis)
            shank = core.fuse(cq.Solid.makeCylinder(1.0, 1.3, cq.Vector(x,y,z), axis))
        else:
            shank = cq.Solid.makeCylinder(1.0, 4, head_origin - axis * 4, axis)
        hardware[f"pcb_screw_{index}"] = cq.Compound.makeCompound([head.fuse(shank), washer])
        if p.insert_diameter is None:
            continue
        # Represent only the installed core. Knurls displace the pilot wall;
        # the catalog specifies the pilot diameter, not the knurl major diameter.
        insert_length = 3.2
        outer = min(mount["parameters"]["insert_diameter"], 3.2)
        origin = cq.Vector(x-insert_length, y, z)
        hardware[f"insert_{index}"] = cq.Solid.makeCylinder(outer/2, insert_length, origin, axis).cut(
            cq.Solid.makeCylinder(1.0, insert_length, origin, axis))
    return hardware


def export_guide_coupon(frame, params, output):
    channel = CrownChannel(params, True)
    x = channel.gate
    y, z, _ = channel.curve(x)
    crop = cq.Workplane('XY').box(11, 18, 8).translate((x, y, z-1.3)).val()
    sample = frame.intersect(crop)
    if not sample.isValid() or len(sample.Solids()) != 1:
        raise ValueError("Invalid wire guide coupon")
    export_mesh(on_print_bed(sample, 0), output / 'wire-guide-coupon.stl')


def export_stencil(outlines, label, output):
    bounds = cq.Compound.makeCompound(outlines).BoundingBox()
    width, height = bounds.xlen + 16, bounds.zlen + 25
    paths = []
    for wire in outlines:
        points, _ = wire.sample(max(32, int(wire.Length() * 3)))
        polygon = " ".join(f"{point.x-bounds.xmin+8:.3f},{bounds.zmax-point.z+8:.3f}"
                           for point in points)
        paths.append(f'<polygon points="{polygon}"/>')
    ruler_y = height - 11
    output.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.3f}mm" '
        f'height="{height:.3f}mm" viewBox="0 0 {width:.3f} {height:.3f}">\n'
        '<g fill="none" stroke="black" stroke-width="0.22">\n'
        + "\n".join(paths)
        + f'<path d="M8,{ruler_y-1}v2m0,-1h20m0,-1v2"/></g>\n'
        f'<text x="32" y="{ruler_y+1.2}" font-size="3" font-family="sans-serif">'
        f'{label} · 20 mm check · Print at 100%</text>\n</svg>\n'
    )


def build(params, mount_x, pcb_step, output, insert_diameter, insert_depth):
    print_dir = output / "print"
    preview_dir = output / "mesh"
    print_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(exist_ok=True)

    optics = build_slim_frame(params, channel_frame(make_shell(params), params))
    printable = {name: as_shape(shape) for name, shape in optics.items()}
    frame = fit_pcb_mount(printable["slim_frame"], mount_x, insert_diameter, insert_depth)
    printable["slim_frame"] = emboss_wordmark(frame, params)
    # The stiff arm roots taper through the soft gasket's outside corners.
    # Trim the foam model to those roots, as with the hand-cut foam blank.
    foam = {
        name: as_shape(shape).cut(printable["slim_frame"]).clean()
        for name, shape in build_foam_reference(params).items()
    }
    mount = design_data(mount_x, insert_diameter, insert_depth)
    elastic = make_strap_references(mount_x)
    harness, wire_data = build_harness(params)
    refs = (
        build_glass_references(params) | make_references(mount_x, pcb_path=pcb_step)
        | foam | elastic | board_fasteners(mount) | plug_backs(mount_x) | harness
    )
    parts = printable | {name: as_shape(shape) for name, shape in refs.items()}
    assembly = cq.Assembly(name="Strobe Glasses MK1 Slim")
    manifest = []
    for name, shape in parts.items():
        solids = shape.Solids()
        if not solids or not shape.isValid() or (name in printable and len(solids) != 1):
            raise ValueError(f"{name}: expected valid solid geometry, found {len(solids)} solids")
        preview = preview_dir / f"{name}.stl"
        export_mesh(shape, preview)
        if name in printable:
            angle = 90 if name == "shared_retainer" else 0
            export_mesh(on_print_bed(shape, angle), print_dir / f"{name}.stl")
        surface = material(name)
        assembly.add(shape, name=name,
                     color=cq.Color(*COLORS[surface], .72 if surface == "glass" else 1.0))
        b = shape.BoundingBox()
        manifest.append({
            "name": name,
            "mesh": str(preview.relative_to(output)),
            "surface": surface,
            "printable": name in printable,
            "size_mm": [round(v, 2) for v in (b.xlen, b.ylen, b.zlen)],
            "volume_mm3": round(shape.Volume(tol=1e-6), 2),
        })

    collisions = {}
    for a, b in combinations(parts, 2):
        volume = overlap(parts[a], parts[b])
        if volume > .01:
            collisions[f"{a} / {b}"] = round(volume, 3)
    for name, envelope in make_keepouts(mount_x).items():
        for part, solid in (printable | elastic).items():
            volume = overlap(as_shape(envelope), solid)
            if volume > .01:
                collisions[f"{name} / {part}"] = round(volume, 3)
    expected_solids = sum(len(shape.Solids()) for shape in parts.values())
    step_file = output / "mk1-bare.step"
    assembly.export(str(step_file))
    imported = cq.importers.importStep(str(step_file)).val()
    if len(imported.Solids()) != expected_solids or not imported.isValid():
        raise ValueError(f"{step_file.name} did not round trip as {expected_solids} valid solids")
    report = {
        "parts": manifest,
        "overlaps_mm3": collisions,
        "frame": design_metadata(params),
        "wordmark": {"text": "rivercraft", "location": "front of right lens rim",
                     "height_above_lens_face_datum_mm": 0.30},
        "mount": mount,
        "harness": {"insulated_diameter_mm": WIRE_OD, "conductors": wire_data},
        "pcb_datum_mm": pcb_location(mount_x).toTuple()[0],
    }
    (output / "geometry.json").write_text(json.dumps(report, indent=2) + "\n")
    for name, (label, outlines) in cut_templates(params).items():
        export_stencil(outlines, label, output / name)
    export_lens_coupon(printable["slim_frame"], printable["shared_retainer"], params, output)
    coupon_dir = output / "snap-test"
    coupon_dir.mkdir(exist_ok=True)
    for name, shape in build_snap_coupon(printable, params).items():
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise ValueError(f"{name}: invalid snap coupon")
        angle = 90 if "retainer" in name else 0
        export_mesh(on_print_bed(shape, angle), coupon_dir / f"{name}.stl")
    strap_dir = output / "strap-test"
    strap_dir.mkdir(exist_ok=True)
    eye_sample = strap_coupon(printable["slim_frame"], mount_x)
    if not eye_sample.isValid() or len(eye_sample.Solids()) != 1:
        raise ValueError("Invalid strap coupon")
    export_mesh(on_print_bed(eye_sample, 0), strap_dir / "strap_anchor_coupon.stl")
    post_sample = mount_coupon(printable["slim_frame"], mount_x)
    if not post_sample.isValid() or len(post_sample.Solids()) != 1:
        raise ValueError("Invalid PCB post coupon")
    export_mesh(on_print_bed(post_sample, 0), output / ("pcb-post-coupon.stl" if insert_diameter is None else "insert-coupon.stl"))
    export_guide_coupon(printable["slim_frame"], params, output)
    if collisions:
        raise ValueError(f"Interferences: {collisions}")
    print(f"Saved {len(printable)} print parts and the bare assembly to {output}")


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--pd", type=float, default=60.8)
    parser.add_argument("--temple-width", type=float, default=126)
    parser.add_argument("--foam-layers", type=int, choices=(1, 2), default=2)
    parser.add_argument("--wrap-degrees", type=float, choices=(0, 20), default=20)
    parser.add_argument("--insert-diameter", type=float, help="Use heat-set posts for PETG instead of the thread-forming screws in resin")
    parser.add_argument("--insert-depth", type=float, default=4.0)
    parser.add_argument("--pcb-step", type=Path, default=HERE / "build/reference/mk1-pcb.step")
    parser.add_argument("--output", type=Path, default=HERE / "build/mk1-bare-resin")
    args = parser.parse_args()
    if not args.pcb_step.is_file():
        parser.error(f"Missing the populated PCB STEP at {args.pcb_step}")
    mount_x = args.temple_width / 2 + TEMPLE_CLEARANCE_PER_SIDE
    params = SlimFrameParams(pd=args.pd, temple_half_width=mount_x,
                            foam_layers=args.foam_layers, wrap_degrees=args.wrap_degrees)
    build(params, mount_x, args.pcb_step, args.output,
          args.insert_diameter, args.insert_depth)


if __name__ == "__main__":
    main()
