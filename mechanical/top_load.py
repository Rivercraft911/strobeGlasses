"""Single-valve MK1 frame with a lift-off brow cap. Dimensions in millimetres."""

from argparse import ArgumentParser
from itertools import combinations
from pathlib import Path

import cadquery as cq
from vtkmodules.vtkFiltersCore import vtkFeatureEdges, vtkPolyDataConnectivityFilter
from vtkmodules.vtkIOGeometry import vtkSTLReader

from build_slim import emboss_wordmark, on_print_bed, overlap
from slim_channel import CrownChannel, brow_z, channel_frame, front_y, swept_profile
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
POST_TOP = 21.8
SCREW_X = 52.65
HEAD_SEAT = POST_TOP + 1.5
COLLAR_R = 1.85
PIN_HEIGHT = 15.5  # Open-ended pin gauge; extension beyond the frame is unrestricted.


def box(w, d, bottom, top, x=0, y=0):
    return _box(w, d, top - bottom, x, y, (bottom + top) / 2).val()


def cylinder(radius, bottom, top, x, y):
    return cq.Solid.makeCylinder(radius, top - bottom, (x, y, bottom))


def keeper_spine(p, clearance=False):
    # Control sections for a single cubic B-spline. Positive offsets from the
    # front datum go toward the face. Four shallow wings reach the glass corners.
    # x, leading edge offset, trailing edge offset, crest above the original brow
    half = [
        (0.0, -1.95, 5.15, 3.00),
        (4.5, -1.85, 6.10, 3.05),
        (9.5, -1.72, 7.95, 3.12),
        (13.5, -1.62, 8.32, 3.16),
        (16.5, -1.56, 7.75, 3.13),
        (21.0, -1.48, 4.85, 3.03),
        (25.0, -1.46, 2.56, 2.80),
        (30.4, -1.48, 2.22, 2.70),
        (35.0, -1.64, 2.48, 2.81),
        (40.0, -2.12, 4.78, 3.04),
        (44.0, -2.90, 7.90, 3.13),
        (47.0, -3.75, 8.52, 3.18),
        (49.0, -4.80, 7.70, 3.24),
        (51.1, -6.30, 3.82, 3.28),
        (53.2, -6.63, 2.05, 3.24),
        (55.0, -6.42, 1.22, 3.00),
        (56.6, -5.00, 0.40, 2.50),
        (57.4, -3.35, -2.55, 1.90),
    ]
    sections = [(-x, *v) for x, *v in reversed(half[1:])] + half
    stations, rows = [], []
    for x, near, far, rise in sections:
        y, z = front_y(p, x), brow_z(p, x)
        width = far - near
        # The underside climbs over the fixed wires. Its low front edge seats in
        # the outside rim. Every feature clears by a straight vertical translation.
        lip = min(width * 0.36, max(0.38, -near - 1.25))
        ramp = min(1.35, (width - lip) * 0.50)
        base = max(POST_TOP + 0.08, z - 0.78) if abs(x) > 49 else z - 0.78
        roof = max(base + 0.72, z + 1.32)
        crest = max(z + rise, roof + 1.28)
        front, back = y - near, y - far
        if clearance:
            extension = max(0, (abs(x) - 55.0) / (57.4 - 55.0)) * 0.35
            x += extension if x > 0 else -extension
            # Move the ramp rearward as well as down so it clears the rising underside.
            lo, hi = base - 0.27, roof - 0.27
            a, b = (x, front + 0.32, lo), (x, front - lip - 0.32, lo)
            c, d = (x, front - lip - ramp - 0.32, hi), (x, back - 0.32, hi)
            row = [
                (a, b),
                (b, (x, b[1] - 0.32 * ramp, lo), (x, c[1] + 0.32 * ramp, hi), c),
                (c, d),
                (d, (x, back - 0.32, 35)),
                ((x, back - 0.32, 35), (x, front + 0.32, 35)),
                ((x, front + 0.32, 35), a),
            ]
        else:

            def pt(t, height):
                return (x, front - width * t, height)

            a = (x, front - lip, base)
            b = (x, front - lip - ramp, roof)
            # A long pitched upper face has one soft highlight. The front radius
            # rolls into it. The rear edge is rounded where fingers lift the cover.
            u = pt(0.22, crest)
            v = pt(0.89, crest - 0.42)
            w = pt(1, roof + 0.35)
            row = [
                ((x, front - 0.18, base), a),
                (a, (x, a[1] - 0.32 * ramp, base), (x, b[1] + 0.32 * ramp, roof), b),
                (b, (x, back + 0.22, roof)),
                ((x, back + 0.22, roof), (x, back + 0.07, roof), (x, back, roof + 0.15), w),
                (w, pt(1, crest - 0.70), pt(0.975, crest - 0.51), v),
                (v, pt(0.70, crest - 0.24), pt(0.39, crest), u),
                (u, pt(0.14, crest), pt(0, base + 1.20), pt(0, base + 0.48)),
                (
                    pt(0, base + 0.48),
                    pt(0, base + 0.20),
                    (x, front - 0.04, base),
                    (x, front - 0.18, base),
                ),
            ]
        stations.append(x)
        rows.append(row)
    return swept_profile(stations, rows, control_sections=True)


def screw_sites(p):
    return [(side * SCREW_X, front_y(p, SCREW_X) + 2.80) for side in (-1, 1)]


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
            # Only the underside touches a raised pane. The oval lands blend
            # into the swept crown above instead of interrupting its top face.
            tab = (
                cq.Workplane("XY", origin=(tab_x, -3.0, CAP_STOP))
                .ellipse(2.85, 1.55)
                .extrude(0.96)
                .faces("<Z")
                .edges()
                .fillet(0.20)
                .val()
            )
            # A narrower stem joins from beneath the skin, keeping all four
            # stops below the continuous upper surface.
            stem_x = lens_point(p, side, edge * 17.40, -2.53, 0)[0]
            stem = (
                cq.Workplane("XY", origin=(tab_x, -2.53, CAP_STOP + 0.62))
                .ellipse(1.78, 0.87)
                .extrude(brow_z(p, stem_x) + 1.73 - CAP_STOP - 0.62)
                .val()
            )
            tab = tab.fuse(stem)
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
                placed(
                    cq.Workplane("XY", origin=(tab_x, -3.0, CAP_STOP - 0.2))
                    .ellipse(3.22, 1.88)
                    .extrude(15)
                    .val()
                ),
                placed(box(2.40, 3.52, 16.65, 32, key_x, PANE_Y)),
            )
    frame = frame.cut(relief)
    for x, y in screw_sites(p):
        frame = frame.cut(cylinder(3.04, POST_TOP, 32, x, y))
        # A tapered boss grows out of the outer rim below the wire trough.
        post = (
            cq.Workplane("XY", origin=(x, y - 6.0, POST_TOP - 10.2))
            .ellipse(4.2, 2.45)
            .workplane(offset=3.6)
            .center(0, 3.9)
            .ellipse(3.85, 3.2)
            .workplane(offset=3.45)
            .center(0, 1.35)
            .ellipse(3.40, 3.18)
            .workplane(offset=3.15)
            .center(0, 0.75)
            .circle(2.97)
            .loft()
            .val()
        )
        # Keep the foot inside the outer skin; added hardware must never form
        # a bump on the original temple's wearer-facing surface.
        side = 1 if x > 0 else -1
        outside = place_at_lens(
            box(150, 80, 5, 35, side * p.pd / 2, p.front_y - 1.15 + 40), p, side
        )
        post = post.intersect(outside)
        if side > 0:
            # The reinforced pilot floor shares the outer shoulder. Carry the
            # original cable trough through its foot, including the crimp passage.
            _, trough = CrownChannel(p, True).shapes()
            post = post.cut(trough)
        frame = frame.fuse(post, cylinder(COLLAR_R, POST_TOP - 0.12, POST_TOP + 0.55, x, y))
        frame = frame.cut(cylinder(RESIN_PILOT_DIAMETER / 2, POST_TOP - 3.95, POST_TOP + 0.8, x, y))
        cap = cap.fuse(cylinder(2.79, POST_TOP, POST_TOP + 2.42, x, y))
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
            lane = 4.10 + (pin - 1) * 1.35
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

        # Unwrap each half into its lens plane. The rear rim sits at -5.70 mm
        # and both straight terminals must stay entirely on the wearer's side.
        half = cap.intersect(box(100, 170, -20, 100, side * 50, 0))
        local = half.rotate((x, p.pivot_y, 0), (x, p.pivot_y, 1), side * p.wrap_degrees)
        if local.BoundingBox().ymin < -5.70 + 0.45:
            raise ValueError("Brow protrudes toward the face beyond its design allowance")
        pins = local.intersect(box(11, 100, -20, 60, x, 0))
        if pins.BoundingBox().ymin < PANE_Y + 2.80:
            raise ValueError("Brow crosses the front of the upright terminal bay")

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
        # Sample just inside each mating face to avoid coplanar Boolean ambiguity.
        seat = cylinder(2.68, POST_TOP + 0.004, POST_TOP + 0.052, x, y).cut(
            cylinder(2.50, POST_TOP + 0.002, POST_TOP + 0.054, x, y)
        )
        for solid, gauge in ((cap, seat), (frame, seat.translate((0, 0, -0.056)))):
            if overlap(solid, gauge) < seat.Volume() * 0.95:
                raise ValueError("Cap and post lack a common bearing surface")
        head_bearing = cylinder(1.675, HEAD_SEAT - 0.10, HEAD_SEAT, x, y)
        if overlap(cap, head_bearing) < 0.215:
            raise ValueError("Insufficient material under the recessed screw head")
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
