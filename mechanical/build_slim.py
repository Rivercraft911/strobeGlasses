"""Export the slim MK1 frame, retainer and assembly in millimetres."""

from argparse import ArgumentParser
from itertools import combinations
import json
from pathlib import Path

import cadquery as cq

from slim_frame import (
    SlimFrameParams, build_foam_reference, build_glass_references,
    build_slim_frame, build_snap_coupon, curved_bridge_band,
    cut_templates, design_metadata, engraving_skin,
)
from slim_mount import (
    TEMPLE_CLEARANCE_PER_SIDE, design_data, insert_coupon, make_keepouts, make_shell, pcb_supports,
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


def engrave_wordmark(frame, params):
    """Cut the lowercase wordmark into the center brow, facing forward."""
    bounds = curved_bridge_band(params, params.front_y + .01, 1.8).val().BoundingBox()
    plane = cq.Plane(origin=(0, bounds.ymax + .1, 18.2),
                     xDir=(-1, 0, 0), normal=(0, 1, 0))
    letters = cq.Workplane(plane).text("rivercraft", 3.7, -bounds.ylen - .2, font="Arial",
                                      kind="bold", combine=False).solids().vals()
    if len(letters) < len("rivercraft"):
        raise ValueError("Incomplete rivercraft engraving")
    stamps = [engraving_skin(frame, letter, (0, -.38, 0)) for letter in letters]
    return frame.cut(*stamps).clean()


def board_fasteners(mount):
    """M2x4 screws and 0.3 mm washers fitted to the actual PCB notches."""
    hardware = {}
    axis = cq.Vector(1, 0, 0)
    for index, site in enumerate(mount["pcb_screws"], 1):
        x, y, z = site["position"]
        washer_origin = cq.Vector(x + 1, y, z)
        washer = cq.Solid.makeCylinder(2.5, .3, washer_origin, axis).cut(
            cq.Solid.makeCylinder(1.1, .3, washer_origin, axis)
        )
        head_origin = cq.Vector(x + 1.3, y, z)
        head = cq.Solid.makeCylinder(1.9, 1.55, head_origin, axis)
        shank = cq.Solid.makeCylinder(1.0, 4, head_origin - axis * 4, axis)
        hardware[f"pcb_screw_{index}"] = cq.Compound.makeCompound([head.fuse(shank), washer])
    return hardware


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

    optics = build_slim_frame(params, make_shell(params))
    printable = {name: as_shape(shape) for name, shape in optics.items()}
    frame = printable["slim_frame"].fuse(pcb_supports(mount_x, insert_diameter, insert_depth)).clean()
    printable["slim_frame"] = engrave_wordmark(frame, params)
    # The stiff arm roots taper through the soft gasket's outside corners.
    # Trim the foam model to those roots, as with the hand-cut foam blank.
    foam = {
        name: as_shape(shape).cut(printable["slim_frame"]).clean()
        for name, shape in build_foam_reference(params).items()
    }
    mount = design_data(mount_x, insert_diameter, insert_depth)
    elastic = make_strap_references(mount_x)
    refs = (
        build_glass_references(params) | make_references(mount_x, pcb_path=pcb_step)
        | foam | elastic | board_fasteners(mount)
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
    step_file = output / "mk1-slim.step"
    assembly.export(str(step_file))
    imported = cq.importers.importStep(str(step_file)).val()
    expected_solids = sum(len(shape.Solids()) for shape in parts.values())
    if len(imported.Solids()) != expected_solids or not imported.isValid():
        raise ValueError(f"{step_file.name} did not round trip as {expected_solids} valid solids")
    report = {
        "parts": manifest,
        "overlaps_mm3": collisions,
        "frame": design_metadata(params),
        "engraving": {"text": "rivercraft", "depth_mm": 0.38},
        "mount": mount,
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
    insert_sample = insert_coupon(printable["slim_frame"], mount_x)
    if not insert_sample.isValid() or len(insert_sample.Solids()) != 1:
        raise ValueError("Invalid insert coupon")
    export_mesh(on_print_bed(insert_sample, 0), output / "insert-coupon.stl")
    if collisions:
        raise ValueError(f"Interferences: {collisions}")
    print(f"Saved {len(printable)} print parts and the assembly to {output}")


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--pd", type=float, default=60.8)
    parser.add_argument("--temple-width", type=float, default=126)
    parser.add_argument("--foam-layers", type=int, choices=(1, 2), default=2)
    parser.add_argument("--wrap-degrees", type=float, choices=(0, 20), default=20)
    parser.add_argument("--insert-diameter", type=float, default=3.8)
    parser.add_argument("--insert-depth", type=float, default=4.0)
    parser.add_argument("--pcb-step", type=Path, default=HERE / "build/reference/mk1-pcb.step")
    parser.add_argument("--output", type=Path, default=HERE / "build/mk1-sculpted")
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
