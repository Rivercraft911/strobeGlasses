"""Check rear loading and latch travel on an exported MK1 assembly (millimetres)."""

import json
from pathlib import Path
import sys

import cadquery as cq

from build_slim import as_shape, overlap
from slim_frame import (
    SlimFrameParams, _box, _snap_offset, build_foam_reference,
    build_glass_references, lens_spacer, place_at_lens, snap_features,
)


def clear(body, envelope, description):
    volume = overlap(body, envelope)
    if volume > .003:
        raise ValueError(f"{description}: {volume:.4f} mm³ interference")


def swept_box(shape, travel, xy_error=0, z_error=0):
    b = shape.BoundingBox()
    return _box(b.xlen + 2 * xy_error, b.ylen + travel, b.zlen + 2 * z_error,
                b.center.x, b.center.y - travel / 2, b.center.z).val()


def panel_checks(frame, p):
    glass = build_glass_references(p)
    for side in (-1, 1):
        x = side * p.pd / 2
        for layer, y, z in (("front", p.pane_y, p.pane_stagger), ("rear", -p.pane_y, 0)):
            pane = _box(p.glass_w, p.glass_thickness, p.glass_h, x, y, z).val()
            tab = _box(1.01, .5, 8, x + p.glass_w / 2 + .495, y, z).val()
            sleeves = [_box(2.4, p.terminal_length, 1.5, x + dx, y - p.terminal_length / 2,
                            z + p.glass_h/2 + .78).val() for dx in (-2.54, 2.54)]
            for part in (pane, tab, *sleeves):
                # A 12 mm straight approach tested with an extra 0.15 mm on
                # both edges along the local horizontal and vertical axes.
                envelope = place_at_lens(swept_box(part, 12, .15, .15), p, side)
                clear(frame, envelope, f"{side} {layer} pane, tab or insulated lead")
            # The terminal datum can move 0.50 mm. Its pitch has a separate
            # 0.50 mm tolerance. Verify the cumulative offset on the second pin.
            for sleeve, error in zip(sleeves, (.50, 1.0)):
                clear(frame, place_at_lens(swept_box(sleeve, 12, error + .15, .15), p, side),
                      "worst-case sleeved terminal insertion")
            far_tab = tab.translate((0, 0, -p.glass_h / 2 + 4.0))
            clear(frame, place_at_lens(swept_box(far_tab, 12, .15, .15), p, side),
                  "edge tab at far corner")
        # Both sets of insulated joints run rearward. Verify their actual
        # separation while the rear pane is being installed behind the front.
        name = "right" if side == 1 else "left"
        rearward = place_at_lens(_box(2.4, p.terminal_length + 12, 1.5,
                                      x - 2.54, -p.pane_y - (p.terminal_length + 12) / 2,
                                      p.glass_h / 2 + .78).val(), p, side)
        gap = as_shape(glass[f"terminal_{name}_front_1"]).distance(rearward)
        if gap < .49:
            raise ValueError(f"{name} solder joint clearance is only {gap:.3f} mm")
        spacer = lens_spacer(p, x)
        clear(frame, place_at_lens(swept_box(spacer.val(), 12), p, side), "spacer insertion")


def check_upper_lip(frame, p):
    # Inspect the brow over the top edge of the maximum front pane, at both
    # ends of its pocket and just outside the intentionally open lead bay.
    top = p.glass_h / 2 + p.pane_stagger + p.pocket_clearance
    for dx in (-18, -15, -6.3, 6.3, 15, 18):
        for y in (p.stop_y + .15, p.pane_y, p.seat_y - .01):
            x = p.pd / 2 + dx
            ray = cq.Edge.makeLine((x, y, top - .001), (x, y, top + 5))
            edges = frame.intersect(place_at_lens(ray, p)).Edges()
            wall = sum(edge.Length() for edge in edges)
            if wall < 1.0:
                raise ValueError(f"Brow over pane at {dx}, {y} is only {wall:.3f} mm")


def clip_checks(frame, retainer, p):
    parts = {k: as_shape(v) for k, v in snap_features(p).items()}
    glass = build_glass_references(p)
    pads = build_foam_reference(p)
    for side, name in ((-1, "left"), (1, "right")):
        hook = parts["hook_" + name]
        if overlap(frame, hook.translate((0, -1.5, 0))) < .05:
            raise ValueError(f"{name} hook fails to catch the frame")
        released = hook.translate((-side * p.latch_deflection, 0, 0))
        clear(frame, swept_box(released, 8, .30, .30), f"{name} release tolerance")
        for layer in ("front", "rear"):
            clear(as_shape(glass[f"lcd_{name}_{layer}"]), swept_box(released, 8),
                  f"{name} release against the glass")

        # Approach the outer thumb land from the wearer side with a 3 mm
        # blunt tool. Stop just short of its outside face.
        xoff, yoff, _ = _snap_offset(p, side)
        outer_x = side * (p.snap_x + 1.685) + xoff
        end = cq.Vector(outer_x + side * 1.3, p.stop_y - p.latch_thickness - .8 + yoff, 9.85)
        start = end + cq.Vector(side * 2.1, -8, 0)
        path = end - start
        access = cq.Solid.makeCylinder(1.5, path.Length, start, path.normalized())
        clear(frame, access, f"{name} thumb-land approach")
        for key, shape in pads.items():
            if name in key:
                clear(as_shape(shape), access, f"{key} thumb-land access")

    # Check the whole rigid carrier and the unloaded beam stems between the
    # seated and withdrawn positions. The two moving hook tips were swept above.
    body = retainer.cut(parts["hook_right"], parts["hook_left"])
    for travel in (.10, .25, .4, .45, .5, .55, .65, .8, 1., 1.5, 2., 3., 4., 6., 8.):
        clear(frame, body.translate((0, -travel, 0)), f"carrier at {travel} mm")


def main(output):
    report = json.loads((output / "geometry.json").read_text())
    f, m = report["frame"], report["mount"]["parameters"]
    p = SlimFrameParams(pd=f["pd"], temple_half_width=m["mount_x"],
                        wrap_degrees=f["lens_wrap_degrees_per_side"], foam_layers=f["foam_layers"])
    assembly = cq.importers.importStep(str(output / "mk1-slim.step")).val()
    frame, retainer = assembly.Solids()[:2]
    panel_checks(frame, p)
    clip_checks(frame, retainer, p)
    check_upper_lip(frame, p)
    print("Panel, tab, sleeve, spacer, clip release and service-access checks passed.")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
