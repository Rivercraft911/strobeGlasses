"""Open lay-in cable trough formed into the fixed crown, in millimetres."""

from math import cos, radians, tan

import cadquery as cq
import numpy as np
from scipy.interpolate import PchipInterpolator
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.Geom import Geom_BSplineSurface
from OCP.gp import gp_Pnt
from OCP.TColgp import TColgp_Array2OfPnt
from OCP.TColStd import TColStd_Array1OfInteger, TColStd_Array1OfReal


def cubic_loft(sections):
    # Limit degree so a dip at the wire guide cannot ripple across the brow.
    builder = BRepOffsetAPI_ThruSections(True, False)
    builder.SetMaxDegree(3)
    for section in sections:
        builder.AddWire(section.wrapped)
    builder.Build()
    return cq.Solid(builder.Shape())


def swept_profile(stations, rows):
    """Cubic Hermite rails with the specified Bezier cross sections, exactly in X."""

    def knots(values, kind):
        result = kind(1, len(values))
        for i, value in enumerate(values, 1):
            result.SetValue(i, value)
        return result

    def cap(row):
        edges = []
        for points in row:
            pts = [cq.Vector(*point) for point in points]
            edges.append(cq.Edge.makeLine(*pts) if len(pts) == 2 else cq.Edge.makeBezier(pts))
        return cq.Face.makeFromWires(cq.Wire.assembleEdges(edges))

    u_knots = knots(stations, TColStd_Array1OfReal)
    u_mult = knots([4] + [3] * (len(stations) - 2) + [4], TColStd_Array1OfInteger)
    v_knots = knots([0.0, 1.0], TColStd_Array1OfReal)
    faces = [cap(rows[0]), cap(rows[-1])]
    for section_curve in zip(*rows):
        coords = np.array(section_curve)
        derivatives = PchipInterpolator(stations, coords, axis=0).derivative()(stations)
        controls = [coords[0]]
        for i, dx in enumerate(np.diff(stations)):
            controls.extend(
                (
                    coords[i] + dx / 3 * derivatives[i],
                    coords[i + 1] - dx / 3 * derivatives[i + 1],
                    coords[i + 1],
                )
            )
        degree = coords.shape[1] - 1
        poles = TColgp_Array2OfPnt(1, len(controls), 1, degree + 1)
        for i, row in enumerate(controls, 1):
            for j, point in enumerate(row, 1):
                poles.SetValue(i, j, gp_Pnt(*point))
        surface = Geom_BSplineSurface(
            poles,
            u_knots,
            v_knots,
            u_mult,
            knots([degree + 1] * 2, TColStd_Array1OfInteger),
            3,
            degree,
        )
        faces.append(cq.Face(BRepBuilderAPI_MakeFace(surface, 1e-7).Face()))
    return cq.Solid.makeSolid(cq.Shell.makeShell(faces))


def front_y(p, x):
    slope = tan(radians(p.wrap_degrees))
    center = p.pivot_y + (p.front_y - p.pivot_y) / cos(radians(p.wrap_degrees)) + slope * p.pd / 2
    dx = abs(x)
    return center - slope * (2.6 + dx * dx / 10.4 if dx < 5.2 else dx)


def brow_z(p, x):
    dx = abs(x) - (p.pd - 60.8) / 2
    return np.interp(
        dx,
        (0, 5.2, 8.4, 11.45, 17, 41, 47, 52.4),
        (21, 21.06, 21.12, 21.76, 22.37, 22.53, 22.70, 22.80),
    ) + 0.42 * (1 - p.wrap_degrees / 20)


class CrownChannel:
    """Sections stay open at the LCD terminals so a whole wired stack lifts out."""

    def __init__(self, p, shoulder):
        shift = (p.pd - 60.8) / 2
        if shoulder:
            self.x = np.array([36.8, 38.3, 40.5, 45, 49, 52, 54, 56, 57.6, 59.3]) + shift
            floor = [brow_z(p, x) - 0.61 for x in self.x[:6]]
            flat = 0.42 * (1 - p.wrap_degrees / 20)
            floor.extend([22.0 + flat, 21.65 + flat, 21.22 + flat, 20.82 + flat])
            front = front_y(p, 52 + shift)
            centers = [front_y(p, x) - 2.8 for x in self.x[:6]] + [
                front - 3.28,
                front - 4.05,
                front - 4.82,
                front - 5.82,
            ]
            self.pitch = 1.18
            self.half = 2.48
        else:
            self.x = np.array(
                [
                    -24.2 - shift,
                    -22.8 - shift,
                    -20 - shift,
                    -16 - shift,
                    -12 - shift,
                    -10 - shift,
                    -8.4 - shift,
                    -5.2,
                    0,
                    5.2,
                    8.4 + shift,
                    10 + shift,
                    12 + shift,
                    16 + shift,
                    20 + shift,
                    22.8 + shift,
                    24.2 + shift,
                ]
            )
            floor = [
                max(brow_z(p, x) - 0.60, 21.56) if abs(x) > 10 + shift else brow_z(p, x) - 0.57
                for x in self.x
            ]
            centers = [
                front_y(p, x) - np.interp(abs(x), (0, 8, 15, 24), (1.52, 1.70, 2.20, 2.35))
                for x in self.x
            ]
            self.pitch = 1.12
            self.half = 1.28
        # The entrances climb back to the original crown and widen slightly.
        floor[0] += 0.72
        floor[1] += 0.28
        floor[-2] += 0.28
        floor[-1] += 0.72
        fade = [0.0, 0.55, *([1.0] * (len(self.x) - 4)), 0.55, 0.0]
        self.curve = PchipInterpolator(self.x, np.column_stack((centers, floor, fade)), axis=0)

        self.gate = 54.6 + shift if shoulder else 0.0
        self.drop = 1.72 if shoulder else 2.10
        # The crimp can travel straight through the short web. The open
        # ramps either side let the flexible wire return to the crown.
        if shoulder:
            self.x = (
                np.array(
                    [
                        36.8,
                        38.3,
                        40.5,
                        45.0,
                        48.5,
                        49.9,
                        51.2,
                        51.8,
                        53.15,
                        54.6,
                        55.95,
                        57.5,
                        58.45,
                        59.3,
                    ]
                )
                + shift
            )
        else:
            self.x = np.sort(np.r_[self.x, -2.7, 2.7, -6.8, 6.8])
        self.shoulder = shoulder

    def depression(self, x):
        delta = x - self.gate
        end = (6.1 if delta < 0 else 4.7) if self.shoulder else 8.4
        t = np.clip((end - abs(delta)) / (end - 2.9), 0, 1)
        return self.drop * t * t * (3 - 2 * t)

    def wire_point(self, x, lane):
        y, floor, _ = self.curve(x)
        return (x, y + self.pitch * lane, floor - self.depression(x) + 0.58)

    def shapes(self):
        outer, cutters = [], []
        for x in self.x:
            y, z, fade = self.curve(x)
            w = self.half + 0.30 * (1 - fade)
            dip = self.depression(x)
            # The visible crown rolls down into the openings. Keep the roof
            # over the crimp passage independent of the lower cable bed.
            lip = 0.04 + 0.80 * fade + (0.66 if self.shoulder else 0.24) * dip / self.drop
            scale = 0.16 + 0.84 * fade
            rim = w * scale

            def skin(a, h):
                return (x, y + a, z - 0.92 * (1 - fade) + h)

            def bed(a, h):
                return (x, y + a, z - dip + h)

            # The ends return inside the existing brow; only the flared entry remains.
            outer.append(
                [
                    [skin(-rim * 0.64, -1.64 - dip), skin(rim * 0.64, -1.64 - dip)],
                    [
                        skin(rim * 0.64, -1.64 - dip),
                        skin(rim + 0.23 * scale, -1.34 - dip),
                        skin(rim + 1.39 * scale, -0.48 - 0.6 * dip),
                        skin(rim + 1.39 * scale, lip - 0.46),
                    ],
                    [
                        skin(rim + 1.39 * scale, lip - 0.46),
                        skin(rim + 1.39 * scale, lip - 0.14),
                        skin(rim + 0.94 * scale, lip),
                        skin(rim + 0.53 * scale, lip),
                    ],
                    [skin(rim + 0.53 * scale, lip), skin(-rim - 0.53 * scale, lip)],
                    [
                        skin(-rim - 0.53 * scale, lip),
                        skin(-rim - 0.94 * scale, lip),
                        skin(-rim - 1.39 * scale, lip - 0.14),
                        skin(-rim - 1.39 * scale, lip - 0.46),
                    ],
                    [
                        skin(-rim - 1.39 * scale, lip - 0.46),
                        skin(-rim - 1.39 * scale, -0.48 - 0.6 * dip),
                        skin(-rim - 0.23 * scale, -1.34 - dip),
                        skin(-rim * 0.64, -1.64 - dip),
                    ],
                ]
            )
            cutters.append(
                [
                    [bed(-w - 0.16, 6), bed(-w - 0.16, 0.44)],
                    [
                        bed(-w - 0.16, 0.44),
                        bed(-w - 0.16, 0.16),
                        bed(-w - 0.04, 0),
                        bed(-w + 0.24, 0),
                    ],
                    [bed(-w + 0.24, 0), bed(w - 0.24, 0)],
                    [bed(w - 0.24, 0), bed(w + 0.04, 0), bed(w + 0.16, 0.16), bed(w + 0.16, 0.44)],
                    [bed(w + 0.16, 0.44), bed(w + 0.16, 6)],
                    [bed(w + 0.16, 6), bed(-w - 0.16, 6)],
                ]
            )
        # Keeping a short strip of the original crown creates a through passage.
        keep = []
        for x in (self.gate - 1.15, self.gate, self.gate + 1.15):
            y, z, _ = self.curve(x)
            ceiling = z - self.depression(x) + 1.95
            keep.append(cq.Workplane("YZ", origin=(x, y, ceiling + 4)).rect(14, 8).val())
        tool = swept_profile(self.x, cutters).cut(cubic_loft(keep))
        return swept_profile(self.x, outer), tool


def channel_frame(frame, p):
    for shoulder in (False, True):
        shell, tool = CrownChannel(p, shoulder).shapes()
        frame = frame.fuse(shell).cut(tool).clean()
    return frame
