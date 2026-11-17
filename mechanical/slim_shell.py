"""Continuous brow, temples and strap eyes. Coordinates are in millimetres."""

from math import cos, radians, tan

import cadquery as cq
import numpy as np
from scipy.interpolate import PchipInterpolator
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.Geom import Geom_BezierSurface
from OCP.TColgp import TColgp_Array2OfPnt
from OCP.gp import gp_Pnt


def _section(front_x, front_y, back_x, back_y, bottom, top, upper_return, lower_return):
    """Bezier control sections for the cheek roll, face, brow and soft back edges."""
    height = top - bottom
    cheek = min(3.2, .18 * height)
    brow = min(4.5, .25 * height)

    def pt(f, z, upper=0, lower=0):
        return gp_Pnt(front_x + f * (back_x - front_x) + upper * upper_return + lower * lower_return,
                      front_y + f * (back_y - front_y), z)

    lower = pt(.31, bottom, lower=.85)
    lower_corner = pt(.14, bottom + .27 * cheek, lower=1)
    face_low = pt(.028, bottom + cheek)
    face_high = pt(.028, top - brow)
    shoulder = pt(.16, top - .21 * brow, 1)
    crest = pt(.43, top, .88)
    crown_back = pt(.83, top)
    inside_high = pt(1, top - .42)
    inside_low = pt(1, bottom + .44)
    sole_back = pt(.81, bottom)
    return (
        (lower, pt(.24, bottom, lower=.95), pt(.17, bottom + .13 * cheek, lower=1.02), lower_corner),
        (lower_corner, pt(.09, bottom + .41 * cheek, lower=.98),
         pt(.04, bottom + cheek * .75), face_low),
        (face_low, pt(.002, bottom + .35 * height),
         pt(.002, bottom + .62 * height), face_high),
        (face_high, pt(.035, top - .68 * brow), pt(.080, top - .30 * brow, .95), shoulder),
        (shoulder, pt(.22, top - .12 * brow, 1.05), pt(.34, top, 1.0), crest),
        (crest, crown_back),
        (crown_back, pt(1, top), inside_high),
        (inside_high, inside_low),
        (inside_low, pt(1, bottom), sole_back),
        (sole_back, lower),
    )


def _surface_patch(control_rows):
    poles = TColgp_Array2OfPnt(1, len(control_rows), 1, len(control_rows[0]))
    for i, row in enumerate(control_rows, 1):
        for j, point in enumerate(row, 1):
            poles.SetValue(i, j, point)
    return cq.Face(BRepBuilderAPI_MakeFace(Geom_BezierSurface(poles), 1e-7).Face())


def _cap(row):
    edges = []
    for points in _section(*row):
        vectors = [cq.Vector(p.X(), p.Y(), p.Z()) for p in points]
        edges.append(cq.Edge.makeBezier(vectors))
    return cq.Face.makeFromWires(cq.Wire.assembleEdges(edges))


def _wing_blank(p):
    theta = radians(p.wrap_degrees)
    slope = tan(theta)
    center = p.pivot_y + (p.front_y - p.pivot_y) / cos(theta) + slope * p.pd / 2
    depth = (p.front_y - p.stop_y - .06) / cos(theta)
    shift = (p.pd - 60.8) / 2
    # The LCD seats follow two planes. Only the central 5.2 mm on each
    # side roll through the bridge in plan. Raise the rear of the bridge so it
    # clears the removable retainer during its straight rearward travel.
    front_rows = (
        (0, 15.70, 21.00, 2.65), (5.2, 12.95, 21.06, 3.08),
        (8.4, 5.7, 21.12, 3.35), (10.1, -8.0, 21.37, 5.20),
        (11.45, -16.65, 21.76, None), (14.5, -19.82, 22.17, None),
        (17, -20.0, 22.37, None), (41.0, -20.0, 22.53, None),
        (46.8, -19.88, 22.70, None), (49.5, -19.65, 22.77, 5.20),
        (52.4, -19.15, 22.80, 2.30),
    )
    rows = []
    for i, (x, low, high, shallow) in enumerate(front_rows):
        x += shift * min(x / 11.45, 1)
        y = center - slope * x
        if x < 5.2:
            y = center - slope * (2.6 + x * x / 10.4)
        # In the flat variant the nasal glass corner sits closer to the low
        # crown. Leave the same printable roof there as in the wrapped frame.
        high += .42 * (1 - p.wrap_degrees / 20) * min(x / 11.45, 1)
        # A flat pane also reaches farther outboard at its rear corner.
        # Carry the pocket wall to that corner before thinning the temple.
        if i == len(front_rows) - 2:
            shallow += (depth - shallow) * (1 - p.wrap_degrees / 20)
        inner_x = x - .80 if i == len(front_rows) - 1 else x
        rows.append((x, y, inner_x, y - (depth if shallow is None else shallow), low, high, 0., 0.))

    fx, fy = rows[-1][:2]
    mount = p.temple_half_width
    # Outer and wearer-side rails reach the thin board floor tangentially.
    # At the tail, increasing the section outward leaves room for folded elastic.
    rows.extend((
        (fx + 5, fy - 2.25, fx + 4.05, fy - 4.02, -17.3, 21.55, 0, 0),
        (mount - 7.0, fy - 6.50, mount - 8.4, fy - 8.20, -15.10, 18.85, 0, 0),
        (mount - 1.7, -18.50, mount - 3.50, -19.42, -13.45, 15.65, 0, 0),
        (mount + 1.1, -26.75, mount - .65, -27.24, -12.35, 13.6, 0.45, 0.42),
        (mount + 1.6, -33.5, mount, -33.5, -11.7, 12.3, 3.8, 1.55),
        (mount + 1.6, -43, mount, -43, -11.45, 11.75, 4.35, 3.9),
        (mount + 1.6, -53, mount, -53, -11.75, 11.9, 3.55, 3.15),
        (mount + 1.6, -59.6, mount, -59.6, -12.40, 12.40, 0.34, 0.33),
        (mount + 2.5, -62.5, mount, -62.5, -12.60, 12.60, 0, 0),
        (mount + 2.5, -69.9, mount, -69.9, -12.60, 12.60, 0, 0),
    ))
    # Cubic rails pass through every station. Converting their endpoint
    # tangents to Bezier poles gives exact CAD surfaces, including the flats.
    # The crown rolls out over the PCB and fairs back in at the strap. Its
    # section remains solid while the inside wall stays clear of the pouch.
    values = np.array(rows)
    centerline = (values[:, :2] + values[:, 2:4]) / 2
    stations = np.r_[0., np.cumsum(np.linalg.norm(np.diff(centerline, axis=0), axis=1))]
    tangents = PchipInterpolator(stations, values, axis=0).derivative()(stations)
    tangents[0, [1, 3, 4, 5]] = 0
    # The planes on either side of the nose have a common tangent at the roll.
    for i in range(1, len(front_rows)):
        tangents[i, 1] = -slope * tangents[i, 0]
        if front_rows[i][3] is None:
            tangents[i, 3] = -slope * tangents[i, 2]
    faces = []
    for i, step in enumerate(np.diff(stations)):
        controls = (values[i], values[i] + step * tangents[i] / 3,
                    values[i+1] - step * tangents[i+1] / 3, values[i+1])
        sections = [_section(*row) for row in controls]
        faces.extend(_surface_patch(poles) for poles in zip(*sections))
    for row in (values[0], values[-1]):
        faces.append(_cap(row))
    return cq.Solid.makeSolid(cq.Shell.makeShell(faces))


def _side_window(mount):
    # Project along the bend. Both rails stay continuous past the PCB edge.
    plane = cq.Plane(origin=(mount - 69, 0, 0), xDir=(.6, -.8, 0), normal=(-.8, -.6, 0))
    return (cq.Workplane(plane).moveTo(41.2, -8.75)
            .bezier([(41.9, -5.7), (46.3, 5.2), (50.2, 9.22)], includeCurrent=True)
            .bezier([(52.6, 11.70), (60.9, 8.24), (66.0, 7.15)], includeCurrent=True)
            .bezier([(68.3, 6.66), (69.1, 4.10), (69.1, 1.35)], includeCurrent=True)
            .bezier([(69.1, -3.6), (68.4, -5.65), (64.9, -6.15)], includeCurrent=True)
            .bezier([(56.1, -7.41), (49.6, -9.92), (43.3, -11.38)], includeCurrent=True)
            .bezier([(41.84, -11.72), (40.78, -10.58), (41.2, -8.75)], includeCurrent=True)
            .close().extrude(130, both=True).val())


def _strap_cuts(mount, center_y, throat, height):
    side = cq.Workplane("YZ", origin=(mount - 3, 0, 0))
    slot = (side.center(center_y, 0).sketch().rect(throat, height)
            .vertices().fillet(1).finalize().extrude(10).val())
    # Round the two free end corners in elevation. The straight load-bearing
    # edge of the eye stays 3.1 mm behind the slot.
    end = (side.center(-69.9 + 5, 0).sketch().rect(10, 25.2).vertices()
           .fillet(1.9).finalize().extrude(10).val())
    rear_block = side.center(-69.9, 0).rect(8, 32).extrude(10).val()
    return slot, rear_block.cut(end)


def continuous_shell(p, center_y, throat, height):
    half = _wing_blank(p)
    window = _side_window(p.temple_half_width)
    half = half.cut(window, *_strap_cuts(p.temple_half_width, center_y, throat, height))
    # Ease both sides of the through slot where the elastic bears on the wall.
    slot_edges = []
    for edge in half.Edges():
        b = edge.BoundingBox()
        if (b.ymin > center_y - throat/2 - .02 and b.ymax < center_y + throat/2 + .02
                and b.zmin > -height/2 - .02 and b.zmax < height/2 + .02 and b.xlen < .8):
            slot_edges.append(edge)
    half = half.fillet(.45, slot_edges)
    return half.fuse(half.mirror("YZ")).clean()
