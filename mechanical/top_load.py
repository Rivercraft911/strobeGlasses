"""Single-valve MK1 frame with a lift-off brow cap. Dimensions in millimetres."""

from argparse import ArgumentParser
from itertools import combinations
from pathlib import Path

import cadquery as cq
from scipy.interpolate import PchipInterpolator
from vtkmodules.vtkFiltersCore import vtkFeatureEdges, vtkPolyDataConnectivityFilter
from vtkmodules.vtkIOGeometry import vtkSTLReader

from build_slim import emboss_wordmark, on_print_bed, overlap
from slim_channel import CrownChannel, brow_z, channel_frame, cubic_loft, front_y
from slim_frame import SlimFrameParams, _aperture, _box, _front_flare, _rounded, place_at_lens
from slim_harness import brow_to_header, lens_point, plug_backs, rounded_path, tube
from slim_mount import (
    RESIN_PILOT_DIAMETER,
    fit_pcb_mount,
    make_keepouts,
    make_references,
    make_shell,
)

FLOOR = -17.1
PANE_Y = -2.9
MEASURED_GLASS = 1.83
SLOT_DEPTH = 2.20
PIN_BAY_BOTTOM = FLOOR + 35.8 - 3.0  # 3 mm below the shortest specified glass.
CAP_STOP = 19.45
POST_TOP = 19.7
SCREW_X = 52.65
HEAD_SEAT = POST_TOP + 1.5
COLLAR_R = 1.85
PIN_HEIGHT = 15.5  # Open-ended pin gauge; extension beyond the frame is unrestricted.


def box(w, d, bottom, top, x=0, y=0):
    return _box(w, d, top - bottom, x, y, (bottom + top) / 2).val()


def cylinder(radius, bottom, top, x, y):
    return cq.Solid.makeCylinder(radius, top - bottom, (x, y, bottom))


def keeper_spine(p, clearance=False):
    # The slim strip runs along the wearer side, winding behind each pair of
    # pins. Its front edge follows the nose roll and drops below the fixed ridge.
    stations = [0, 5.2, 11, 18, 25, 35.5, 42, 48, SCREW_X]
    near = PchipInterpolator(stations, [4.95, 5.2, 6.65, 8.20, 10.75, 10.75, 8.65, 8.35, 8.35])
    sections = []
    for x in [-v for v in reversed(stations[1:])] + stations:
        y = front_y(p, x) - float(near(abs(x))) - 1.12
        z = brow_z(p, x) - 1.30
        depth, bottom, top = 2.24, z - 1.00, z + 1.00
        if clearance:
            depth, bottom, top = depth + 0.55, bottom - 0.20, 32.0
        wire = cq.Workplane("YZ", origin=(x, y, (top + bottom) / 2)).rect(depth, top - bottom).val()
        sections.append(wire.fillet2D(0.35, wire.Vertices()))
    return cubic_loft(sections)


def screw_sites(p):
    return [(side * SCREW_X, front_y(p, SCREW_X) - 9.45) for side in (-1, 1)]


def build_parts(p):
    frame = channel_frame(make_shell(p), p)
    cap = keeper_spine(p)
    relief = keeper_spine(p, clearance=True)
    for side in (-1, 1):
        x = side * p.pd / 2

        def placed(shape):
            return place_at_lens(shape, p, side)

        # Fixed, rounded rear flange closes the U-shaped rails. The panel sits
        # just behind the original cable troughs so those keep their full floors.
        rear = _rounded(41.0, 40.10, 3.35, -0.70, 5.00, x, 0.55)
        rear = rear.faces("<Y").edges().fillet(0.48).val()
        frame = frame.fuse(placed(rear))
        bore = _aperture(p, p.front_y + 0.5, 15, x).val()
        frame = frame.cut(placed(bore), placed(_front_flare(p, x).val()))
        # A 1 mm fill seal can lead on either side. The cap cheeks locate
        # the tab-free ends of the panel once it reaches the bottom seat.
        width = p.glass_w + 2 * (p.pocket_clearance + 1.0)
        frame = frame.cut(placed(box(width, SLOT_DEPTH, FLOOR, 60, x, PANE_Y)))
        mouth = (
            cq.Workplane("XY", origin=(x, PANE_Y, 19.25))
            .rect(width, SLOT_DEPTH)
            .workplane(offset=2.6)
            .rect(width + 0.6, SLOT_DEPTH + 0.6)
            .loft(ruled=True)
            .val()
        )
        frame = frame.cut(placed(mouth))
        # Entirely open to the sky, also while the keeper is installed.
        # A little extra width accommodates pin pitch and solder sleeves.
        frame = frame.cut(placed(box(12.6, 6.8, PIN_BAY_BOTTOM, 60, x, PANE_Y)))
        for edge in (-1, 1):
            tab_x = x + edge * 17.40
            tab = (
                cq.Workplane("XY")
                .box(5.25, 5.95, 2.20)
                .edges("|Z")
                .fillet(0.75)
                .edges("not |Z")
                .fillet(0.22)
                .translate((tab_x, -4.98, CAP_STOP + 1.10))
                .val()
            )
            key_x = x + edge * (p.glass_w / 2 + p.pocket_clearance + 0.8)
            tip = (
                cq.Workplane("XY", origin=(key_x, PANE_Y, 17.0))
                .center(edge * 0.45, 0)
                .rect(0.70, 2.72)
                .workplane(offset=1.45)
                .center(-edge * 0.45, 0)
                .rect(1.60, 2.72)
                .loft(ruled=True)
                .val()
            )
            key = tip.fuse(box(1.60, 2.72, 18.45, CAP_STOP + 0.65, key_x, PANE_Y))
            cap = cap.fuse(placed(tab), placed(key))
            frame = frame.cut(
                placed(box(5.85, 6.55, CAP_STOP - 0.2, 32, tab_x, -4.98)),
                placed(box(2.40, 3.52, 16.65, 32, key_x, PANE_Y)),
            )
    frame = frame.cut(relief)
    for x, y in screw_sites(p):
        frame = frame.cut(cylinder(3.04, POST_TOP, 32, x, y))
        post = (
            cq.Workplane("XY")
            .box(5.6, 9.2, 5.3)
            .edges("|Z")
            .fillet(2.35)
            .faces("<Z")
            .edges()
            .fillet(0.55)
            .translate((x, y + 1.9, POST_TOP - 2.65))
            .val()
        )
        # The temple becomes thin here. Anchor each post into the front skin
        # below the wire bed, leaving the original shoulder passage open above.
        foot = (
            cq.Workplane("XY")
            .box(5.0, 7.15, 2.85)
            .edges("|Z")
            .fillet(1.5)
            .edges("not |Z")
            .fillet(0.36)
            .translate((x, y + 5.30, 16.1))
            .val()
        )
        frame = frame.fuse(post, foot, cylinder(COLLAR_R, POST_TOP - 0.12, POST_TOP + 0.55, x, y))
        frame = frame.cut(cylinder(RESIN_PILOT_DIAMETER / 2, POST_TOP - 3.95, POST_TOP + 0.8, x, y))
        ear = (
            cq.Workplane("XY", origin=(x, y, POST_TOP))
            .circle(2.82)
            .extrude(3.35)
            .faces(">Z")
            .edges()
            .fillet(0.28)
            .val()
        )
        cap = cap.fuse(ear)
        # One round socket, one longitudinally relieved socket for resin shrinkage.
        travel = 0.40 if x > 0 else 0.0
        for radius, bottom, top in (
            (COLLAR_R + 0.22, POST_TOP - 0.1, POST_TOP + 0.75),
            (1.20, POST_TOP - 0.1, 30),
            (2.02, HEAD_SEAT, 30),
        ):
            if travel:
                tool = (
                    cq.Workplane("XY", origin=(x, y, bottom))
                    .slot2D(2 * radius + 2 * travel, 2 * radius)
                    .extrude(top - bottom)
                    .val()
                )
            else:
                tool = cylinder(radius, bottom, top, x, y)
            cap = cap.cut(tool)
    frame = fit_pcb_mount(emboss_wordmark(frame.clean(), p), p.temple_half_width, None, 4.0)
    return frame.clean(), cap.clean()


def glass_references(p):
    refs = {}
    for side, eye in ((-1, "left"), (1, "right")):
        x = side * p.pd / 2
        top = FLOOR + p.glass_h
        pane = box(p.glass_w, MEASURED_GLASS, FLOOR, top, x, PANE_Y)
        tab = box(1.02, 0.65, FLOOR + 7, FLOOR + 15, x + p.glass_w / 2 + 0.49, PANE_Y)
        refs["valve_" + eye] = place_at_lens(pane.fuse(tab), p, side)
        for pin, dx in enumerate((-2.54, 2.54), 1):
            sleeve = box(1.40, 0.65, top, top + PIN_HEIGHT, x + dx, PANE_Y)
            refs[f"lead_{eye}_{pin}"] = place_at_lens(sleeve, p, side)
    return refs


def routed_leads(p):
    bridge, shoulder = CrownChannel(p, False), CrownChannel(p, True)
    wires = {}
    for side, eye, header_z in ((-1, "left", -2.6), (1, "right", 3.55)):
        for pin, dx in enumerate((-2.54, 2.54), 1):
            top = FLOOR + p.glass_h + PIN_HEIGHT
            x, y, z = lens_point(p, side, dx, PANE_Y, top)
            lane = (0.55 + (pin - 1) * 1.65) if side < 0 else (3.15 + (pin - 1) * 1.15)
            front = front_y(p, x) - lane
            crown = brow_z(p, x) + 1.0
            # The free insulated lead bends over toward the fixed ridge. The
            # metal terminal stays vertical; the keeper lifts behind this loop.
            start = [(x, y, z), (x, y, z + 2.0), (x, front, z + 2.0), (x, front, crown)]
            route = start + brow_to_header(p, side, pin, header_z, bridge, shoulder)
            wires[f"wire_{eye}_{pin}"] = tube(rounded_path(route, 2.4)[0])
    return wires


def check_fit(p, frame, cap):
    def clear(solid, gauge, description):
        v = overlap(solid, gauge)
        if v > 0.003:
            raise ValueError(f"{description}: {v:.3f} mm³ collision")

    for solid in (frame, cap):
        if len(solid.Solids()) != 1 or not solid.isValid():
            raise ValueError("Expected a single valid solid per printed part")
    for dz in (0, 0.15, 0.65, 1.0, 2.0, 3.0, 5.0, 12.0):
        clear(frame, cap.translate((0, 0, dz)), f"Cap at {dz} mm lift")

    for side in (-1, 1):
        x = side * p.pd / 2
        top = FLOOR + p.glass_h

        def placed(s):
            return place_at_lens(s, p, side)

        # Sweep the maximum glass AND a full-thickness tab on either edge from
        # completely above the brow to the floor, with 0.15 mm lateral and 0.075 mm face allowance.
        slide = placed(box(p.glass_w + 2.30, p.glass_thickness + 0.15, FLOOR, top + 45, x, PANE_Y))
        clear(frame, slide, "Continuous glass and fill-tab path")
        pane = box(p.glass_w, MEASURED_GLASS, FLOOR, top, x, PANE_Y)
        clear(
            cap,
            placed(box(p.glass_w + 0.30, p.glass_thickness + 0.15, FLOOR, top + 0.15, x, PANE_Y)),
            "Cap over maximum glass",
        )
        # Fifteen mm from the electrode edge to the nearest end of the tab.
        clear(
            cap,
            placed(
                box(p.glass_w + 2.30, p.glass_thickness + 0.15, FLOOR, top - 15 + 0.15, x, PANE_Y)
            ),
            "Cap over seated fill tab",
        )
        for dx in (-2.54, 2.54):
            # Cumulative terminal position/pitch error, sleeving, and bend tolerance.
            for solid in (frame, cap):
                clear(
                    solid,
                    placed(box(4.7, 5.5, PIN_BAY_BOTTOM + 0.10, top + 50, x + dx, PANE_Y)),
                    "Wired terminal entry or cap clearance",
                )
        for dx, dy, dz, solid in (
            (0, 0, 1, cap),
            (0, 0, -0.5, frame),
            (0, 1, 0, frame),
            (0, -1, 0, frame),
            (0.8, 0, 0, cap),
            (-0.8, 0, 0, cap),
        ):
            if overlap(solid, placed(pane.translate((dx, dy, dz)))) < 0.15:
                raise ValueError(f"Pane escaped its intended stop at {(dx, dy, dz)}")
        # Fixed rails on both front and rear faces at the service edges.
        for dx in (-17.0, 17.0):
            for y0 in (PANE_Y - SLOT_DEPTH / 2 - 0.78, PANE_Y + SLOT_DEPTH / 2 + 0.03):
                rail = placed(box(0.35, 0.75, -10, 11, x + dx, y0 + 0.375))
                if overlap(frame, rail) < rail.Volume() - 0.01:
                    raise ValueError("Side guide has less than 0.75 mm of continuous land")
    # Test the original bridge and shoulder routes with actual 0.8 mm wire
    # envelopes. Measure supporting floors and the retaining roofs in each gate.
    for shoulder, lanes in ((False, (-0.5, 0.5)), (True, (-1.5, -0.5, 0.5, 1.5))):
        channel = CrownChannel(p, shoulder)
        for lane in lanes:
            wire = tube(rounded_path([channel.wire_point(x, lane) for x in channel.x], 3.0)[0])
            clear(frame, wire, "Cable trough")
            clear(cap, wire, "Keeper over wire route")
            x, y, z = channel.wire_point(channel.gate, lane)
            for a, b in ((z - 1.3, z - 0.61), (z + 1.51, z + 2.10)):
                gauge = cylinder(0.10, a, b, x, y)
                if overlap(frame, gauge) < gauge.Volume() - 0.001:
                    raise ValueError("Crown cable guide lost its floor or roof")
    for x, y in screw_sites(p):
        clear(cap, cylinder(1.0, HEAD_SEAT - 4, HEAD_SEAT, x, y), "Screw shank in cap")
        clear(cap, cylinder(1.675, HEAD_SEAT + 0.005, HEAD_SEAT + 1.605, x, y), "Screw head")
        clear(cap, cylinder(1.90, HEAD_SEAT + 1.60, HEAD_SEAT + 25, x, y), "Driver access")
        clear(
            frame,
            cylinder(RESIN_PILOT_DIAMETER / 2 - 0.01, HEAD_SEAT - 4, POST_TOP + 0.55, x, y),
            "Pilot",
        )
        floor = cylinder(0.70, POST_TOP - 4.95, POST_TOP - 3.96, x, y)
        if overlap(frame, floor) < floor.Volume() - 0.003:
            raise ValueError("Pilot floor below cap screw is too thin")
    for label, gauge in make_keepouts(p.temple_half_width).items():
        clear(frame, gauge, label)
        clear(cap, gauge, label)


def print_mesh(part, path):
    # OCC can produce small open loops at a blend even when the solid is valid.
    if not on_print_bed(part, 0).exportStl(
        str(path), tolerance=0.04, angularTolerance=0.16, relative=False
    ):
        raise RuntimeError(f"Could not write {path}")
    mesh = vtkSTLReader()
    mesh.SetFileName(str(path))
    mesh.MergingOn()
    edges = vtkFeatureEdges()
    edges.SetInputConnection(mesh.GetOutputPort())
    edges.BoundaryEdgesOn()
    edges.NonManifoldEdgesOn()
    edges.ManifoldEdgesOff()
    edges.FeatureEdgesOff()
    edges.Update()
    components = vtkPolyDataConnectivityFilter()
    components.SetInputConnection(mesh.GetOutputPort())
    components.SetExtractionModeToAllRegions()
    components.Update()
    if edges.GetOutput().GetNumberOfCells() or components.GetNumberOfExtractedRegions() != 1:
        raise ValueError(f"Expected one closed, manifold shell in {path}")


def export_parts(output, p, frame, cap, pcb_step=None):
    refs = glass_references(p)
    wires = routed_leads(p)
    plugs = plug_backs(p.temple_half_width)
    for name, wire in wires.items():
        _, eye, pin = name.split("_")
        header = "J3" if eye == "left" else "J4"
        if (
            wire.distance(refs[f"lead_{eye}_{pin}"]) > 0.005
            or wire.distance(plugs[f"plug_{header}_{eye}"]) > 0.005
        ):
            raise ValueError(f"{name} does not meet both terminals")
        if overlap(frame, wire) > 0.003:
            raise ValueError(f"{name} fouls the fixed frame")
        for lift in (0, 0.5, 2, 4, 8, 12, 16, 18, 22):
            if overlap(cap.translate((0, 0, lift)), wire) > 0.003:
                raise ValueError(f"{name} fouls the keeper at {lift} mm lift")
    for (a, first), (b, second) in combinations(wires.items(), 2):
        if first.distance(second) < 0.015:
            raise ValueError(f"Insulated leads touch: {a}, {b}")
    refs.update(wires)
    for name in ("plug_J3_left", "plug_J4_right"):
        refs[name] = plugs[name]
    for i, (x, y) in enumerate(screw_sites(p), 1):
        head = cylinder(1.675, HEAD_SEAT, HEAD_SEAT + 1.60, x, y)
        # Model the core inside the resin pilot and the major diameter in free air.
        shank = cylinder(0.77, HEAD_SEAT - 4, POST_TOP + 0.55, x, y)
        refs[f"cap_screw_{i}"] = head.fuse(shank, cylinder(1.0, POST_TOP + 0.55, HEAD_SEAT, x, y))
    if pcb_step:
        if not pcb_step.is_file():
            raise FileNotFoundError(pcb_step)
        electronics = make_references(p.temple_half_width, pcb_step)
        for name, solid in electronics.items():
            if overlap(frame, solid) > 0.01 or overlap(cap, solid) > 0.01:
                raise ValueError(f"{name} intersects a printed part")
        refs.update(electronics)
    output.mkdir(exist_ok=True, parents=True)
    assembly = cq.Assembly(name="Strobe Glasses Top Load")
    for name, part, color in (
        ("top_load_frame", frame, (0.16, 0.17, 0.18)),
        ("brow_cap", cap, (0.23, 0.24, 0.25)),
    ):
        assembly.add(part, name=name, color=cq.Color(*color))
        print_mesh(part, output / f"{name}.stl")
    for name, part in refs.items():
        color = (0.20, 0.32, 0.30) if name.startswith("valve_") else (0.55, 0.51, 0.42)
        assembly.add(part, name=name, color=cq.Color(*color))
    assembly.export(str(output / "top_load.step"))


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "build/mk1-top-load")
    parser.add_argument(
        "--pcb-step", type=Path, help="Populated MK1 board at the documented KiCad origin"
    )
    args = parser.parse_args()
    p = SlimFrameParams()
    frame, cap = build_parts(p)
    print("Checking top loading and cap fit", flush=True)
    check_fit(p, frame, cap)
    export_parts(args.output, p, frame, cap, args.pcb_step)
    print(f"Saved frame and cap to {args.output}")


if __name__ == "__main__":
    main()
