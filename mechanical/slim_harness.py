"""Installed wire envelopes. Axes are X across the brow, Y forward, Z up."""

from math import acos, cos, radians, sin, tan

import cadquery as cq
from slim_channel import CrownChannel, brow_z, front_y


WIRE_OD = 0.80  # Maximum insulated diameter in the JST SH drawing.
# Mating faces from the populated MK1 STEP in the mounted coordinate system.
PLUG_AXIS_OFFSET_X = 9.15
EYE_HEADER_FACE_Y = -18.17
BATTERY_HEADER_FACE_Z = -4.85
BATTERY_PLUG_Y = -40.875
PLUG_PROJECTION = 2.0


def rounded_path(points, bend):
    """Straight tangents and true circular bends, limited by adjacent cutbacks."""
    pts = [cq.Vector(*v) for v in points]
    last = pts[0]
    edges = []
    radii = []
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        before, after = b - a, c - b
        vin, vout = before.normalized(), after.normalized()
        angle = acos(max(-1.0, min(1.0, vin.dot(vout))))
        if angle < 0.002:
            continue
        setback = min(bend * tan(angle / 2), before.Length * 0.48, after.Length * 0.48)
        radius = setback / tan(angle / 2)
        start, end = b - vin * setback, b + vout * setback
        mid = b + (vout - vin).normalized() * (radius * (1 / cos(angle / 2) - 1))
        edges.extend((cq.Edge.makeLine(last, start), cq.Edge.makeThreePointArc(start, mid, end)))
        last = end
        radii.append(radius)
    edges.append(cq.Edge.makeLine(last, pts[-1]))
    return cq.Wire.assembleEdges(edges), min(radii)


def tube(path):
    start = path.positionAt(0)
    section = cq.Wire.makeCircle(WIRE_OD / 2, start, path.tangentAt(0))
    return cq.Solid.sweep(section, [], path, True, False)


def lens_point(p, side, offset, y, z):
    angle = radians(-side * p.wrap_degrees)
    dy = y - p.pivot_y
    return (
        side * p.pd / 2 + offset * cos(angle) - dy * sin(angle),
        p.pivot_y + offset * sin(angle) + dy * cos(angle),
        z,
    )


def brow_to_header(p, side, pin, header_z, bridge, shoulder):
    """Wire centerline stations common to both frames, from the brow to the PCB."""
    shift = (p.pd - 60.8) / 2
    mount = p.temple_half_width
    extra_crown = .50 * (1 - p.wrap_degrees / 20)
    points = []
    col = pin - 1
    row = 1 if side < 0 else 0
    if side < 0:
        for x in bridge.x:
            points.append(bridge.wire_point(x, 0.5 - col))
        # Pass the service opening in front of the right LCD terminals.
        for x in (28 + shift, 34 + shift):
            points.append((x, front_y(p, x) - (0.86 + 1.12 * col), brow_z(p, x) + 0.60))
    for x in shoulder.x:
        points.append(shoulder.wire_point(x, 2 * row - 0.5 - col))
    points.append(
        (
            mount - 6,
            front_y(p, 52 + shift) - 7.8 + 2.6 * row - 0.5 * col,
            19.95 + 1.2 * col + extra_crown,
        )
    )
    pin_z = header_z + (pin - 1.5)
    points.extend(
        [
            (mount - 2 + 0.8 * col, -15.8 + 3 * row - 0.65 * col, 16.6 + 1.35 * col),
            (mount + 1.6 + 1.25 * col, -17.5 + 3.5 * row - 0.3 * col, 13.3 + 1.25 * col),
            (mount + 4 + 1.2 * col, -16.6 + 4.2 * row, 9.3 + 1.5 * col),
            (mount + 6.5 + 1.3 * col, -12.3 + 4.5 * row, 6.9 - 5.9 * row + 1.65 * col),
            (mount + PLUG_AXIS_OFFSET_X, -9.6 + 3.8 * row - 0.1 * col, pin_z),
            (mount + PLUG_AXIS_OFFSET_X, EYE_HEADER_FACE_Y + PLUG_PROJECTION, pin_z),
        ]
    )
    return points


def build_harness(p):
    parts, report = {}, {}
    mount = p.temple_half_width
    bridge = CrownChannel(p, False)
    shoulder = CrownChannel(p, True)

    def add(name, points, bend):
        path, radius = rounded_path(points, bend)
        parts[name] = tube(path)
        report[name] = dict(
            length_mm=round(path.Length(), 2), min_center_radius_mm=round(radius, 2)
        )

    for side, eye, header, header_z in ((-1, "left", "J3", -2.6), (1, "right", "J4", 3.55)):
        for pin, offset in enumerate((-2.54, 2.54), 1):
            front_z = p.glass_h / 2 + 0.78 + p.pane_stagger
            rear_z = front_z - p.pane_stagger
            # Each jumper joins the two same-numbered sleeved terminals within the bay.
            back = -p.pane_y - p.terminal_length
            turn_y = back - 0.52
            radius = (front_z - rear_z) / 2

            def at(y, z):
                return cq.Vector(*lens_point(p, side, offset - 0.53, y, z))

            a, b = at(turn_y, front_z), at(turn_y, rear_z)
            path = cq.Wire.assembleEdges(
                [
                    cq.Edge.makeLine(at(p.pane_y - p.terminal_length, front_z), a),
                    cq.Edge.makeThreePointArc(a, at(turn_y - radius, rear_z + radius), b),
                    cq.Edge.makeLine(b, at(back, rear_z)),
                ]
            )
            name = f"jumper_{eye}_{pin}"
            parts[name] = tube(path)
            report[name] = dict(length_mm=round(path.Length(), 2), min_center_radius_mm=radius)

            # Both wires emerge through the open end of the front sleeve,
            # side by side. The jumper stays low while the pigtail turns up.
            start = lens_point(p, side, offset + 0.53, p.pane_y - p.terminal_length, front_z)
            turn = lens_point(p, side, offset + 0.53, p.pane_y - p.terminal_length - 2.15, front_z)
            lift = (turn[0], turn[1], brow_z(p, turn[0]) + 0.56)
            points = [start, turn, lift]
            points.extend(brow_to_header(p, side, pin, header_z, bridge, shoulder))
            add(f"wire_{header}_{eye}_{pin}", points, 3.0)
    # The drawing puts the wires side by side across the narrow end of the
    # pouch. The two curves leave that face normally and meet J2 on axis.
    for pin in (1, 2):
        k = pin - 1.5
        first = cq.Vector(mount + 3.35, -37.2, 1.85 + k)
        lift = 2.2 if pin == 1 else 3.0
        before = cq.Vector(mount + 4.15 + 1.4 * k, -34.85 + 1.15 * k, -4.95 - 0.2 * k)
        corner = cq.Vector(
            mount + 5.55 + 1.15 * k, -37.90 + 0.9 * k, -7.88 - 0.65 * k + (0.25 if pin == 2 else 0)
        )
        end = cq.Vector(
            mount + PLUG_AXIS_OFFSET_X, BATTERY_PLUG_Y + k, BATTERY_HEADER_FACE_Z - PLUG_PROJECTION
        )
        segments = [
            cq.Edge.makeBezier([first, first + cq.Vector(0, lift, 0), before, corner]),
            cq.Edge.makeBezier(
                [corner, corner + (corner - before) * 0.36, cq.Vector(end.x, end.y, -10), end]
            ),
        ]
        path = cq.Wire.assembleEdges(segments)
        name = f"wire_J2_battery_{pin}"
        parts[name] = tube(path)
        max_curvature = max(edge.curvatureAt(t / 100) for edge in segments for t in range(101))
        report[name] = dict(
            length_mm=round(path.Length(), 2), min_center_radius_mm=round(1 / max_curvature, 2)
        )
    return parts, report


def plug_backs(mount):
    """Exposed portions of mated SHR-02V-S-B housings, with their pull ears.

    The connector drawing gives 6.25 mm mated versus 4.25 mm bare header.
    The remaining plug volume is inside the populated PCB's header model.
    """

    stem = cq.Workplane("XY").box(2.1, 1.15, 3).translate((0, 0.575, 0))
    ears = cq.Workplane("XY").box(2.8, 0.85, 5).translate((0, 1.575, 0))
    plug = stem.union(ears).val()
    return {
        "plug_J3_left": plug.translate((mount + PLUG_AXIS_OFFSET_X, EYE_HEADER_FACE_Y, -2.6)),
        "plug_J4_right": plug.translate((mount + PLUG_AXIS_OFFSET_X, EYE_HEADER_FACE_Y, 3.55)),
        "plug_J2_battery": plug.rotate((0, 0, 0), (1, 0, 0), -90).translate(
            (mount + PLUG_AXIS_OFFSET_X, BATTERY_PLUG_Y, BATTERY_HEADER_FACE_Z)
        ),
    }
