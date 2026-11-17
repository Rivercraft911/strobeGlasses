"""Thin rims for two stacks of Adafruit 3627 LCD valves.

X runs across the face, Y points forward, and Z points up. The front and
the retainer are printed parts. Cut foam pads stick to the retainer.
"""

from dataclasses import dataclass
from math import cos, radians, sin, tan

import cadquery as cq


@dataclass(frozen=True)
class SlimFrameParams:
    pd: float = 60.8
    temple_half_width: float = 69.0
    front_y: float = 3.6
    glass_w: float = 36.2
    glass_h: float = 36.2
    glass_thickness: float = 2.0
    pane_gap: float = 0.5
    pane_stagger: float = 1.5
    pocket_clearance: float = 0.30
    seat_y: float = 2.50
    stop_y: float = -2.60
    aperture_w: float = 32.0
    aperture_h: float = 28.3
    front_entry_w: float = 33.4
    front_entry_h: float = 29.5
    retainer_thickness: float = 1.05
    latch_thickness: float = 1.25
    latch_deflection: float = 0.60
    latch_beam_width: float = 1.30
    foam_thickness: float = 3.175
    foam_layers: int = 2
    wrap_degrees: float = 20.0
    terminal_length: float = 3.5

    @property
    def pane_y(self):
        return (self.glass_thickness + self.pane_gap) / 2

    @property
    def foam_y(self):
        return self.stop_y - self.retainer_thickness

    @property
    def pivot_y(self):
        return -self.pane_y - self.glass_thickness / 2

    @property
    def snap_x(self):
        return self.pd / 2 + 21.05


def _xz(y, x=0, z=0):
    return cq.Workplane(cq.Plane(origin=(x, y, z), xDir=(1, 0, 0), normal=(0, -1, 0)))


def _box(width, depth, height, x=0, y=0, z=0):
    return cq.Workplane("XY").box(width, depth, height).translate((x, y, z))


def _rounded(width, height, radius, y, depth, x=0, z=0):
    return (_xz(y, x, z).sketch().rect(width, height).vertices()
            .fillet(radius).finalize().extrude(depth))


def place_at_lens(shape, p, side=1, wrap_fraction=1.0):
    x = side * p.pd / 2
    return shape.rotate((x, p.pivot_y, 0), (x, p.pivot_y, 1),
                        -side * p.wrap_degrees * wrap_fraction)


def _snap_offset(p, side=1):
    # The snaps translate with their rims but stay parallel for shared removal.
    theta = radians(p.wrap_degrees)
    dx = p.snap_x - p.pd / 2
    dy = p.stop_y - p.pivot_y
    return (side * (cos(theta) * dx + sin(theta) * dy - dx),
            cos(theta) * dy - sin(theta) * dx - dy, 0)


def curved_bridge_band(p, face_y, axial_depth):
    """Connect the two lens planes with a tangent transition across the nose."""
    theta = radians(p.wrap_degrees)
    slope = tan(theta)
    half_width = p.pd / 2 - p.glass_w / 2 + 5.0
    ease = 5.2
    center = p.pivot_y + (face_y - p.pivot_y) / cos(theta) + slope * p.pd / 2
    inner = center - slope * ease
    outer = center - slope * half_width
    depth = axial_depth / cos(theta)
    return (cq.Workplane("XY", origin=(0, 0, -24)).moveTo(-half_width, outer)
            .lineTo(-ease, inner).bezier([(0, center), (ease, inner)], includeCurrent=True)
            .lineTo(half_width, outer).lineTo(half_width, outer - depth)
            .lineTo(ease, inner - depth)
            .bezier([(0, center - depth), (-ease, inner - depth)], includeCurrent=True)
            .lineTo(-half_width, outer - depth).close().extrude(48))


def _rim(p):
    # Use full corner arcs and a soft roll at the visible edge. The glass
    # cavity is cut separately so the curves do not dictate its shape.
    corners = [(-20.85, -20.70), (20.85, -20.70), (21.10, 22.20), (-20.85, 22.12)]
    rim = (_xz(p.front_y, p.pd / 2).sketch().polygon(corners).vertices()
           .fillet(5.0).finalize().extrude(p.front_y - p.stop_y))
    return rim.faces(">Y").edges().fillet(1.15)


def _aperture(p, y, depth, x=0):
    return _rounded(p.aperture_w, p.aperture_h, 3.6, y, depth, x, -.25)


def _front_flare(p, x):
    front = _rounded(p.front_entry_w, p.front_entry_h, 4.25,
                     p.front_y + .02, .05, x, -.25)
    back = _aperture(p, p.seat_y, .05, x)
    return cq.Workplane(obj=cq.Solid.makeLoft(
        [part.faces(">Y").wires().val() for part in (front, back)], ruled=True))


def _glass_cavity(p, x):
    depth = p.seat_y - p.stop_y + .10
    width = p.glass_w + 2 * p.pocket_clearance
    height = p.glass_h + p.pane_stagger + 2 * p.pocket_clearance
    cavity = _rounded(width, height, .25, p.seat_y, depth, x, p.pane_stagger / 2)
    # Reserve both sides for the 1 mm polarizer tab.
    for side in (-1, 1):
        tab = _box(1.5, depth, 14, x + side * (width / 2 + .25),
                   p.seat_y - depth / 2, .8)
        cavity = cavity.union(tab)
    return cavity


def _bridge(p):
    # A horizontal tangent at the apex and near-vertical shoulders blend
    # the opening into the inner edges of the rims.
    half = p.pd / 2 - p.glass_w / 2 + 5.0
    band = curved_bridge_band(p, p.front_y, 2.65)
    bounds = band.val().BoundingBox()
    shoulder = [(2.55, 15.9), (6.9, 12.4), (10.1, 4.3),
                (9.35, -7.3), (10.1, -15.6), (half, -16.5)]
    profile = (_xz(bounds.ymax + .5).moveTo(0, 15.9)
               .bezier(shoulder, includeCurrent=True)
               .lineTo(half, 21.95).threePointArc((0, 21.57), (-half, 21.95))
               .lineTo(-half, -16.5)
               .bezier([(-x, z) for x, z in reversed(shoulder[:-1])] + [(0, 15.9)],
                       includeCurrent=True))
    bridge = profile.close().extrude(bounds.ylen + 1).intersect(band).val()
    edge_bounds = [(edge, edge.BoundingBox()) for edge in bridge.Edges()]
    nose_edges = [edge for edge, box in edge_bounds
                  if box.xlen > 1 and box.zmin < 15.9 and -8 < box.zmax <= 16]
    return cq.Workplane(obj=bridge.fillet(.5, nose_edges))


def _receiver(p):
    # The catch housing tapers into the temple in front and thickens toward
    # the retaining shoulder. It extends behind the rim only at the latch.
    stations = ((1.70, 3.0, 8.7, -.47), (-.35, 5.35, 9.2, .24),
                (p.stop_y - .30, 5.6, 9.5, .25))
    sections = [
        _rounded(width, height, 1.05, y, .05, p.snap_x + offset, 10.9)
        .faces(">Y").wires().val()
        for y, width, height, offset in stations
    ]
    return cq.Workplane(obj=cq.Solid.makeLoft(sections, ruled=False))


def cut_snap_channels(frame, p):
    # Allow the tip to deflect inward by 0.60 mm during insertion.
    x = p.snap_x
    # Leave the inside open near the yawed seat. Only the outer catch carries
    # the load. The low rear entry also clears straight retainer withdrawal.
    passage = _box(5.35, 3.7, 3.55, x - 1.925, -1.225, 11.1)
    catch = _box(2.90, 1.99, 3.25, x - .05, -.675, 11.1)
    entry = _box(6.0, 1.40, 10.4, x - 2.2, p.stop_y - .3, 10.9)
    cuts = (passage, catch, entry)
    return frame.cut(*(piece.translate(_snap_offset(p)).val() for piece in cuts),
                     *(piece.mirror("YZ").translate(_snap_offset(p, -1)).val()
                       for piece in cuts)).clean()


def snap_features(params=None):
    """The flexible beams and their forward-facing hooks, in installed position."""
    p = params or SlimFrameParams()
    x = p.snap_x
    beam = _rounded(p.latch_beam_width, 18.1, .32, p.stop_y,
                    p.latch_thickness, x, 3.8)
    # Coordinates are offsets from the beam centre in X and absolute in Y.
    ramp = [(-.65, p.stop_y - .08), (.65, p.stop_y - .08), (.65, -1.60),
            (1.25, -1.48), (1.25, -.79), (.65, .38), (-.65, .38)]
    hook = (cq.Workplane("XY", origin=(x, 0, 9.85)).polyline(ramp)
            .close().extrude(2.5))
    return {"beam_right": beam.translate(_snap_offset(p)),
            "hook_right": hook.translate(_snap_offset(p)),
            "beam_left": beam.mirror("YZ").translate(_snap_offset(p, -1)),
            "hook_left": hook.mirror("YZ").translate(_snap_offset(p, -1))}


def _retainer(p):
    x = p.pd / 2
    ring = _rounded(37.8, 39.0, 3.2, p.stop_y, p.retainer_thickness, x, .75)
    ring = ring.faces("<Y").edges().fillet(.18)
    ring = ring.cut(_aperture(p, p.stop_y + .1, p.retainer_thickness + .2, x))
    inner_edges = [edge for edge in ring.faces("<Y").edges().vals()
                   if edge.BoundingBox().xmin >= x - p.aperture_w / 2 - .01
                   and edge.BoundingBox().xmax <= x + p.aperture_w / 2 + .01]
    ring = cq.Workplane(obj=ring.val().fillet(.18, inner_edges))
    ring = ring.cut(_box(10.0, 2.2, 5.0, x, p.stop_y - .5, 20.25))
    root = _rounded(3.5, 3.8, .60, p.stop_y, p.retainer_thickness,
                     p.snap_x - .96, -3.7)
    ring = place_at_lens(ring.union(root), p)
    retainer = ring.union(ring.mirror("YZ"))
    half = p.pd / 2 - p.glass_w / 2 + 5.0
    band = curved_bridge_band(p, p.stop_y, p.retainer_thickness)
    bounds = band.val().BoundingBox()
    bridge = (_xz(bounds.ymax + .5).moveTo(-half, 14.5)
              .threePointArc((0, 17.4), (half, 14.5))
              .lineTo(half, 17.3).threePointArc((0, 20.2), (-half, 17.3))
              .close().extrude(bounds.ylen + 1).intersect(band))
    retainer = retainer.union(bridge)
    for piece in snap_features(p).values():
        retainer = retainer.union(piece)
    return retainer


def build_slim_frame(params=None):
    p = params or SlimFrameParams()
    if p.front_y - p.seat_y < 1.0:
        raise ValueError("The front lens seat needs at least 1 mm of material")
    rim = place_at_lens(_rim(p), p)
    retainer = _retainer(p)
    receiver = _receiver(p).translate(_snap_offset(p))
    seat = _rounded(38.1, 39.3, 3.3, p.stop_y + .12, 4, p.pd / 2, .75)
    receiver = receiver.cut(place_at_lens(seat, p))
    body = rim.union(rim.mirror("YZ")).union(_bridge(p))
    # The cuff runs into the temple while its inner edge adjoins the thin rim.
    body = body.union(receiver).union(receiver.mirror("YZ"))
    for side in (-1, 1):
        x = side * p.pd / 2
        body = body.cut(place_at_lens(_aperture(p, p.front_y + .1, 10, x), p, side))
        body = body.cut(place_at_lens(_front_flare(p, x), p, side))
        body = body.cut(place_at_lens(_glass_cavity(p, x), p, side))
        # Contact the lower edge of the raised front panel at two discrete stops.
        for dx in (-10, 10):
            foot = _box(4.6, 1.4, 2.05, x + dx, 1.75, -17.825)
            body = body.union(place_at_lens(foot, p, side))
        # Cable exits are open to the brow above the protected wire joints.
        exit_channel = _rounded(10.0, 5.1, .60, 1.45, 5.8, x, 20.2)
        body = body.cut(place_at_lens(exit_channel, p, side))
    front = cut_snap_channels(body.val(), p)
    return {"slim_frame": cq.Workplane(obj=front), "shared_retainer": retainer}


def build_glass_references(params=None):
    p = params or SlimFrameParams()
    parts = {}
    for side, name in ((-1, "left"), (1, "right")):
        x = side * p.pd / 2
        for layer, y, z in (("front", p.pane_y, p.pane_stagger), ("rear", -p.pane_y, 0)):
            glass = _box(p.glass_w, p.glass_thickness, p.glass_h, x, y, z)
            tab = _box(1.01, .5, 8, x + p.glass_w / 2 + .495, y, z)
            parts[f"lcd_{name}_{layer}"] = place_at_lens(glass.union(tab), p, side)
            # Shortened leads plus the insulating sleeve at each solder joint.
            for pin, offset in enumerate((-2.54, 2.54), 1):
                sleeve = _box(
                    2.4, p.terminal_length, 1.5, x + offset, y - p.terminal_length / 2,
                    z + p.glass_h / 2 + .78)
                parts[f"terminal_{name}_{layer}_{pin}"] = place_at_lens(sleeve, p, side)
    return parts


def _foam(p, x):
    pad = _rounded(37.6, 38.8, 4.6, p.foam_y, p.foam_thickness, x, .75)
    inside = _rounded(33.2, 29.6, 4.8, p.foam_y + .1, p.foam_thickness + .2, x, -.25)
    relief = _box(10.5, p.foam_thickness + .2, 4.4,
                  x, p.foam_y - p.foam_thickness / 2, 20.0)
    return pad.cut(inside).cut(relief)


def _face_pad(p, x):
    # Preserve a 2.2 mm side web while stepping the inner edge away from the eye.
    y = p.foam_y - p.foam_thickness
    outside = _rounded(39.4, 40.4, 4.8, y, p.foam_thickness, x, .75)
    inside = _rounded(35.0, 31.6, 5.4, y + .1, p.foam_thickness + .2, x, -.25)
    return outside.cut(inside)


def build_foam_reference(params=None):
    p = params or SlimFrameParams()
    layers = (_foam,) if p.foam_layers == 1 else (_foam, _face_pad)
    return {f"foam_{name}_{layer}": place_at_lens(profile(p, side * p.pd / 2), p, side)
            for side, name in ((-1, "left"), (1, "right"))
            for layer, profile in enumerate(layers, 1)}


def cut_templates(p):
    """Return flat outlines for the foam and optical separator stock."""
    x = p.pd / 2
    base, face = _foam(p, x), _face_pad(p, x)
    shim_y = p.foam_y - 4
    temple = face.intersect(_box(10, 8, 26, x + 19.6, shim_y, 1))
    cheek = face.intersect(_box(26, 8, 8, x + 4, shim_y, -17.5))
    # Both staggered panes cover this outline. The inner hole clears the
    # optical bore, and the outer edge avoids both of the lower pane stops.
    separator = _rounded(35.7, 33.8, 1.1, 0, p.pane_gap, x, .75)
    separator = separator.cut(_rounded(33.2, 29.6, 4.25, .05, .6, x, -.25))
    profiles = {
        "foam-template.svg": ("Base pads", (base,)),
        "foam-face-template.svg": ("Face pads", (face,)),
        "foam-shim-template.svg": ("Cheek and temple shims", (cheek, temple)),
        "valve-spacer-template.svg": ("0.5 mm valve spacers", (separator,)),
    }
    return {
        name: (label, [wire for profile in pieces for part in (profile, profile.mirror("YZ"))
                       for wire in part.faces(">Y").wires().vals()])
        for name, (label, pieces) in profiles.items()
    }


def design_metadata(params=None):
    p = params or SlimFrameParams()
    foam_stack = p.foam_layers * p.foam_thickness
    glass_to_retainer = -p.pane_y - p.glass_thickness / 2 - p.foam_y
    return {
        "units": "mm",
        "pd": p.pd,
        "lens_wrap_degrees_per_side": p.wrap_degrees,
        "local_front_face_y": p.front_y,
        "clear_aperture": [p.aperture_w, p.aperture_h],
        "maximum_pane": [p.glass_w, p.glass_h, p.glass_thickness],
        "pocket_clearance_per_side": p.pocket_clearance,
        "pane_gap": p.pane_gap,
        "pane_stagger": p.pane_stagger,
        "front_seat_thickness": p.front_y - p.seat_y,
        "front_pane_axial_clearance": p.seat_y - p.pane_y - p.glass_thickness / 2,
        "rear_pane_axial_clearance": -p.pane_y - p.glass_thickness / 2 - p.stop_y,
        "rigid_optical_depth": p.front_y - p.foam_y,
        "foam_layers": p.foam_layers,
        "foam_layer_thickness": p.foam_thickness,
        "foam_base_opening": [33.2, 29.6],
        "foam_face_opening": [35.0, 31.6],
        "foam_to_rear_glass_unloaded": glass_to_retainer + foam_stack,
        "total_optical_depth": p.front_y - p.foam_y + foam_stack,
        "remaining_terminal_length": p.terminal_length,
        "retainer_thickness": p.retainer_thickness,
        "latch_thickness": p.latch_thickness,
        "latch_deflection": p.latch_deflection,
    }


def build_snap_coupon(printable, params=None):
    p = params or SlimFrameParams()
    clip = _box(9.8, 9, 25.6, p.snap_x - 2.4, -.5, 4.2).translate(_snap_offset(p)).val()
    return {"snap_receiver_coupon": printable["slim_frame"].intersect(clip),
            "snap_retainer_coupon": printable["shared_retainer"].intersect(clip)}
