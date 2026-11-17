"""Open, integral MK1 PCB rails and a non-clamping protected-cell saddle.

No electronics enclosure, lid, temple joint, or temple fasteners. Fuse the two
returned shapes into slim_frame's rigid wings. Global X lateral/Y forward/Z up.
Local u=Y+66, v=Z, w=X-mount_x.
The PCB keeps its original datum Y=-37.4 and bottom X=mount_x+6.6.
The PCB closes the battery pocket when tightened onto the standoffs.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
from math import dist
import cadquery as cq

from slim_frame import SlimFrameParams, place_at_lens

PCB_NOTCHES=((19.4,-7.625),(32.5,7.625))
BATTERY_SIZE = (22.0, 11.5, 3.5)
BATTERY_CENTER = (17.8, 1.85)
POCKET_CLEARANCE = 0.3
POCKET_RIM_GAP = 0.35
TEMPLE_CLEARANCE_PER_SIDE = 6.0
STRAP_NOMINAL_WIDTH = 19.05
STRAP_MAX_WIDTH = 20.0
STRAP_SLOT_HEIGHT = 20.8
STRAP_SLOT_THROAT = 4.2
STRAP_SLOT_CENTER = 1.3
STRAP_EYE_DEPTH = 2.5

@dataclass(frozen=True)
class MountParams:
    mount_x: float=69.0
    insert_diameter: float=3.8
    insert_depth: float=4.0
    insert_outer_diameter: float=3.6
    insert_radial_wall: float=1.3
    board_floor: float=6.6
    floor: float=1.6


def _box(u,v,w,du,dv,dw):
    return cq.Workplane('XY').box(du,dv,dw,centered=(False,False,False)).translate((u,v,w)).val()


def _roundrect(u,v,w,du,dv,h,r):
    return cq.Workplane('XY').workplane(offset=w).center(u,v).rect(du,dv).extrude(h).edges('|Z').fillet(r).val()


def _cylinder(u,v,w,r,h):
    return cq.Solid.makeCylinder(r,h,cq.Vector(u,v,w))


def place(shape,mount_x=69.0,side='right'):
    shape=shape.rotate((0,0,0),(1,1,1),120).translate((mount_x,-66,0))
    return shape if side=='right' else shape.mirror('YZ')


def pcb_location(mount_x=69.0):
    return cq.Location(cq.Vector(mount_x+6.6,-37.4,0),cq.Vector(1,1,1),120)


def _strap_eye():
    # Keep the forward end at u=6.5, which clears the leadless end of the pouch.
    # The longer eye preserves a 3.1 mm bar on each side of the wider throat.
    outer = _roundrect(STRAP_SLOT_CENTER, 0, 0, 10.4, 26.8, STRAP_EYE_DEPTH, 2)
    aperture = _roundrect(STRAP_SLOT_CENTER, 0, -.2,
                          STRAP_SLOT_THROAT, STRAP_SLOT_HEIGHT, STRAP_EYE_DEPTH + .4, 1)
    return cq.Workplane(obj=outer.cut(aperture)).edges("not |Z").fillet(.55).val()


def _temple_sweep(mount_x, frame_params=None):
    # Start inside the rim with the top edge at the brow. The lower edge
    # sweeps up into the carrier while the top rolls around the temple.
    stations = (
        (3.12, 49.98, 2.02, -13.90, 19.95),
        (1.55, 51.80, 2.45, -13.57, 20.12),
        (0.00, 53.26, 2.85, -12.85, 19.99),
        (-5.00, 57.60, 3.14, -9.53, 18.69),
        (-10.00, 61.38, 3.11, -6.42, 16.18),
        (-14.50, 65.28, 2.81, -5.65, 13.76),
        (-19.00, 68.35, 2.35, -7.27, 11.83),
        (-22.50, 69.57, 1.82, -9.70, 10.81),
        (-25.50, 69.80, 1.60, -10.60, 10.60),
        (-28.50, 69.80, 1.60, -10.60, 10.60),
    )
    p = frame_params or SlimFrameParams()
    wires = []
    for y, x, width, bottom, top in stations:
        # The front follows the valve center. The back follows the temple width.
        # Ease between the two without pulling the front section out of the rim.
        t = min(1.0, max(0.0, (1.55 - y) / 27.05))
        blend = t * t * (3 - 2 * t)
        offset = (p.pd - 60.8) / 2 * (1 - blend) + (mount_x - 69) * blend
        section = _roundrect(0, 0, 0, width, top - bottom, .05, .40 * width)
        wire = cq.Workplane(obj=section).faces('<Z').val().outerWire()
        wire = wire.rotate((0, 0, 0), (1, 0, 0), 90).translate(
            (x + offset, y, (bottom + top) / 2))
        wires.append(place_at_lens(wire, p, wrap_fraction=1 - blend))
    temple = cq.Solid.makeLoft(wires, ruled=False)
    # Continuous tangents at the four joins give the opening a softer sweep.
    relief = (cq.Workplane("YZ", origin=(mount_x - 16.0, -0.12 * p.wrap_degrees, 0))
              .moveTo(-6.10, -1.65)
              .bezier([(-5.35, -.60), (-4.55, 6.85), (-5.35, 8.60)],
                      includeCurrent=True)
              .bezier([(-6.15, 10.35), (-13.57, 8.55), (-15.40, 6.95)],
                      includeCurrent=True)
              .bezier([(-17.23, 5.35), (-17.65, 2.27), (-16.25, 1.15)],
                      includeCurrent=True)
              .bezier([(-14.85, .03), (-6.85, -2.70), (-6.10, -1.65)],
                      includeCurrent=True)
              .close().extrude(20.0)).val()
    return temple.cut(relief).clean()


def _battery_pocket(p):
    u, v = BATTERY_CENTER
    length, width, _ = BATTERY_SIZE
    length += 2 * POCKET_CLEARANCE
    width += 2 * POCKET_CLEARANCE
    wall = 1.0
    bottom = p.floor - .2
    top = p.board_floor - POCKET_RIM_GAP
    rim = _roundrect(u, v, bottom, length + 2 * wall, width + 2 * wall,
                     top - bottom, 1.15)
    cavity = _roundrect(u, v, bottom - .1, length, width, top - bottom + .2, .22)
    # Open the lead exit down to the floor so the pocket can drain through it.
    # The end wall across the rest of the pack stops the pouch.
    lead_exit = _box(28.4, -5.7, p.floor, 2.4, 9.2, top - p.floor + .1)
    # Lower the rear rim locally under the USB plug, leaving a full height shoulder.
    usb_relief = _box(4.5, -5.7, 4.2, 2.5, 11.95, top - 4.1)
    return rim.cut(cavity, lead_exit, usb_relief)


def _right_local(p,electronics=True):
    # The flat carrier supports the battery and the board standoffs.
    carrier=_roundrect(25,0,0,40,21.2,p.floor,2.1).fuse(_strap_eye())
    if electronics:
        carrier = carrier.fuse(_battery_pocket(p))
        # Cap the battery gap with a slim rail below the board plane. The
        # slopes fade back into the carrier ahead of both connector zones.
        rail_profile = [(7.5, 1.36), (7.5, 1.63), (11.4, 6.24),
                        (36.5, 6.24), (44.6, 1.60), (44.6, 1.36)]
        rail = (cq.Workplane("XZ", origin=(0, 10.05, 0))
                .polyline(rail_profile).close().extrude(1.35)).val()
        carrier = carrier.fuse(rail)
    boss_radius=max(p.insert_outer_diameter,p.insert_diameter)/2+p.insert_radial_wall
    for u,v in (PCB_NOTCHES if electronics else ()):
        carrier=carrier.fuse(_cylinder(u,v,0,boss_radius,p.board_floor))
        # Forward 45-degree ramp supports the tall insert post when the fused
        # frame prints front-face-down. No independent post support forest.
        # Start inside the boss so the join has area, rather than a tangent edge.
        ramp_start=u+boss_radius-.8
        ramp_end=u+boss_radius+(p.board_floor-p.floor)
        ramp=cq.Workplane('XZ').polyline([(ramp_start,0),(ramp_end,0),
             (ramp_end,p.floor),(ramp_start,p.board_floor)]).close().extrude(2.4,both=True).val()
        carrier=carrier.fuse(ramp.translate((0,v,0)))
    # Blind insert pilots with a short lead-in through every unioned support.
    for u,v in (PCB_NOTCHES if electronics else ()):
        pilot = _cylinder(u, v, p.board_floor - p.insert_depth,
                          p.insert_diameter / 2, p.insert_depth + .2)
        lead_in = cq.Solid.makeCone(p.insert_diameter / 2, p.insert_diameter / 2 + .22,
                                    .35, cq.Vector(u, v, p.board_floor - .35))
        carrier = carrier.cut(pilot, lead_in)
    return carrier.clean()


def _left_local(p):
    # Keep the same exterior on both sides, with insert posts on the right.
    return _right_local(p,electronics=False)


def battery_lead_points(mount_x=69.0):
    """Leave the pouch forward, then go under the PCB edge into J2."""
    return [(mount_x+3.35,-37.2,1.85), (mount_x+3.8,-36.5,1.85),
            (mount_x+5.46,-36.1,-8.5), (mount_x+9.3,-40.875,-10.7)]


def _wire_corridor(points,radius=1.25):
    tube=None
    for first,last in zip(points,points[1:]):
        a,b=cq.Vector(first),cq.Vector(last);delta=b-a
        segment=cq.Solid.makeCylinder(radius,delta.Length,a,delta.normalized())
        segment=segment.fuse(cq.Solid.makeSphere(radius,a)).fuse(cq.Solid.makeSphere(radius,b))
        tube=segment if tube is None else tube.fuse(segment)
    return tube.clean()


def make_mounts(mount_x=69.0,insert_diameter=3.8,insert_depth=4.0, *, frame_params=None):
    """Two integral frame extensions, not separately screwed-on parts."""
    p=MountParams(mount_x,insert_diameter,insert_depth)
    temple = _temple_sweep(mount_x, frame_params)
    right=place(_right_local(p),mount_x).fuse(temple)
    left=place(_left_local(p),mount_x,'left').fuse(temple.mirror('YZ'))
    return {'right_pcb_rail':right.clean(), 'left_strap_wing':left.clean()}


def make_references(mount_x=69.0,pcb_path=None):
    if pcb_path and Path(pcb_path).exists():
        pcb=cq.importers.importStep(str(pcb_path)).val().moved(pcb_location(mount_x))
    else:
        pcb=_roundrect(28.6,0,6.6,41.2,15.25,1,1.2)
        for u,v in PCB_NOTCHES:
            pcb=pcb.cut(_cylinder(u,v,6.5,1.2,1.3))
        pcb=place(pcb,mount_x)
    p = MountParams(mount_x)
    u, v = BATTERY_CENTER
    length, width, height = BATTERY_SIZE
    battery = place(_box(u - length / 2, v - width / 2, p.floor,
                         length, width, height), mount_x)
    return {'pcb':pcb, 'battery':battery}


def make_keepouts(mount_x=69.0):
    """SH plugs and a representative USB-C cable overmold at its mouth."""
    return {'J2_plug_wire':place(_box(22.8,-10.7,7.6,4.7,5.85,3.4),mount_x),
            'J3_plug_wire':place(_box(47.8,-5,7.6,6.2,4.8,3.4),mount_x),
            'J4_plug_wire':place(_box(47.8,1.15,7.6,6.2,4.8,3.4),mount_x),
            'USB_C_overmold':place(_box(-15,-6.23,4.7,21.5,12,8),mount_x),
            'battery_lead_corridor':_wire_corridor(battery_lead_points(mount_x),0.9)}


def design_data(mount_x=69.0,insert_diameter=3.8,insert_depth=4.0):
    p=MountParams(mount_x,insert_diameter,insert_depth)
    route=battery_lead_points(mount_x)
    return {'parameters':asdict(p),
            'pcb_screws':[{'axis':'X','position':(mount_x+6.6,u-66,v)} for u,v in PCB_NOTCHES],
            'board_bottom_x':mount_x+p.board_floor,'battery_max_mm':BATTERY_SIZE,
            'battery_pocket_inner_mm':tuple(size + 2 * POCKET_CLEARANCE for size in BATTERY_SIZE[:2]),
            'battery_pocket_rim_gap_mm':POCKET_RIM_GAP,
            'battery_to_pcb_mm':p.board_floor - p.floor - BATTERY_SIZE[2],
            'battery_free_lead_min_mm':18.5,'battery_lead_points':route,
            'battery_lead_route_polyline_mm':sum(dist(a,b) for a,b in zip(route,route[1:])),
            'hardware':'2x M2x4 pan-head screw, head≤5mm;2x M2x3 insert(OD3.6);optional0.3–0.5mm nylon washers,OD≤5mm',
            'thread_engagement_with_washer_mm':(2.5,2.7),
            'fit_temple_width_mm':2 * (mount_x - TEMPLE_CLEARANCE_PER_SIDE),
            'arm_inside_span_mm':2 * mount_x,
            'strap_anchor_outside_span_mm':2 * (mount_x + STRAP_EYE_DEPTH),
            'strap_width_mm':STRAP_NOMINAL_WIDTH,
            'strap_slot_throat_mm':STRAP_SLOT_THROAT,
            'strap_slots':{side:{'center':(sign * (mount_x + STRAP_EYE_DEPTH / 2),
                                           STRAP_SLOT_CENTER - 66, 0),
                                 'long_axis':'Z','clear_height':STRAP_SLOT_HEIGHT,'exit':'rearward'}
                           for side, sign in (('right', 1), ('left', -1))},
            'foam_pad_landings':{'right':((mount_x,-33,-6),(mount_x,-21,6)),
                                 'left':((-mount_x,-33,-6),(-mount_x,-21,6))},
            'battery_retention':'Pocket walls capture the pouch under the PCB on its two existing screws',
            'notes':['Fuse both returned rails into slim_frame. No side-joint fasteners or electronics lid.',
                     'Black resin default: bond3.6mm OD M2x3 inserts into3.8x4mm pockets; hold tops flush during cure. Never heat-install into cured resin.',
                     'PETG option: insert_diameter=3.2 for heat-setting the same insert; print a fit coupon first.',
                     'Both arms share the same mirrored outline. The battery pocket and insert posts are on the right.',
                     'USB-C,SW1/SW2,D1,TP1/TP2/TP3 and SH connectors remain exposed.',
                     'Slot and pilot fit require a printer/material coupon before final fabrication.']}


def make_strap_references(mount_x=69.0, thickness=1.8, width=STRAP_MAX_WIDTH):
    """Short single-pass elastic tails; no assumed full head circumference."""
    bridge_u=STRAP_SLOT_CENTER-thickness/2
    tail_length=18+STRAP_SLOT_CENTER+thickness/2
    band=_box(-18,-width/2,-thickness,tail_length,width,thickness)
    band=band.fuse(_box(-18,-width/2,STRAP_EYE_DEPTH,tail_length,width,thickness))
    band=band.fuse(_box(bridge_u,-width/2,-thickness,thickness,width,
                       STRAP_EYE_DEPTH+2*thickness))
    return {'right_elastic_tail':place(band,mount_x),
            'left_elastic_tail':place(band,mount_x,'left')}


def strap_coupon(mount_x):
    """Right strap anchor and its transition into the flat temple arm."""
    coupon = _right_local(MountParams(mount_x), electronics=False).intersect(
        _box(-5, -15, -1, 17, 30, 5))
    return place(coupon, mount_x)
