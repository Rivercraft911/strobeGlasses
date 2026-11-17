"""PCB supports, battery pocket, hardware and connector envelopes for MK1."""

from dataclasses import dataclass, asdict
from pathlib import Path
import cadquery as cq

from slim_shell import continuous_shell

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

# McMaster 96817A204 forms its threads in a #52 pilot (0.0635 inches).
RESIN_PILOT_DIAMETER = .0635 * 25.4
RESIN_PILOT_DEPTH = 4.6

@dataclass(frozen=True)
class MountParams:
    mount_x: float=69.0
    insert_diameter: float | None=None
    insert_depth: float=4.0
    boss_diameter: float=6.4
    board_floor: float=6.6
    floor: float=1.6

    @property
    def pilot(self):
        if self.insert_diameter is None:
            return RESIN_PILOT_DIAMETER, RESIN_PILOT_DEPTH
        return self.insert_diameter, self.insert_depth


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
    floor = _roundrect(u, v, .9, length + 1.6, width + 1.6, p.floor - .9, 1.0)
    return rim.cut(cavity, lead_exit, usb_relief).fuse(floor)


def _pcb_supports(p):
    carrier = _battery_pocket(p)
    diameter, depth = p.pilot
    boss_radius = max(p.boss_diameter / 2, diameter / 2 + 1.3)
    for u, v in PCB_NOTCHES:
        post = _cylinder(u, v, 0, boss_radius, p.board_floor)
        # Spread the screw load into the arm. Both tapered feet lie beneath
        # the board and clear the pouch, its lead exit and the terminal plugs.
        foot = cq.Solid.makeCone(boss_radius + .85, boss_radius, 2.75, cq.Vector(u, v, .25))
        carrier = carrier.fuse(post, foot)
    for u,v in PCB_NOTCHES:
        pilot = _cylinder(u, v, p.board_floor - depth, diameter/2, depth + .2)
        lead_in = cq.Solid.makeCone(diameter/2, diameter/2 + .22, .25,
                                    cq.Vector(u, v, p.board_floor - .25))
        carrier = carrier.cut(pilot, lead_in)
    return carrier.clean()


def make_shell(params):
    return continuous_shell(params, STRAP_SLOT_CENTER - 66, STRAP_SLOT_THROAT, STRAP_SLOT_HEIGHT)


def pcb_supports(mount_x, insert_diameter, insert_depth):
    return place(_pcb_supports(MountParams(mount_x, insert_diameter, insert_depth)), mount_x)


def fit_pcb_mount(frame, mount_x, insert_diameter, insert_depth):
    p = MountParams(mount_x, insert_diameter, insert_depth)
    frame = frame.fuse(pcb_supports(mount_x, insert_diameter, insert_depth))
    # Trim the swept arm and both post feet back to the pocket floor. Leave the
    # same clearance during insertion that the seated pouch has at its edges.
    length, width, _ = BATTERY_SIZE
    cavity = _roundrect(*BATTERY_CENTER, p.floor, length + 2 * POCKET_CLEARANCE,
                        width + 2 * POCKET_CLEARANCE, p.board_floor + 10, .22)
    return frame.cut(place(cavity, mount_x)).clean()


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
    return {'J2_plug_wire':place(_box(22.4,-10.7,7.6,5.45,5.85,3.4),mount_x),
            'J3_plug_wire':place(_box(47.8,-5.35,7.6,6.2,5.5,3.4),mount_x),
            'J4_plug_wire':place(_box(47.8,.80,7.6,6.2,5.5,3.4),mount_x),
            'USB_C_overmold':place(_box(-15,-6.23,4.7,21.5,12,8),mount_x)}


def design_data(mount_x=69.0,insert_diameter=None,insert_depth=4.0):
    p=MountParams(mount_x,insert_diameter,insert_depth)
    return {'parameters':asdict(p),
            'pcb_screws':[{'axis':'X','position':(mount_x+6.6,u-66,v)} for u,v in PCB_NOTCHES],
            'board_bottom_x':mount_x+p.board_floor,'battery_max_mm':BATTERY_SIZE,
            'battery_pocket_inner_mm':tuple(size + 2 * POCKET_CLEARANCE for size in BATTERY_SIZE[:2]),
            'battery_pocket_rim_gap_mm':POCKET_RIM_GAP,
            'battery_to_pcb_mm':p.board_floor - p.floor - BATTERY_SIZE[2],
            'battery_free_lead_min_mm':18.5,
            'hardware':{**({'insert': 'McMaster 94459A767, M2 x 3.2 heat-set'}
                           if insert_diameter is not None else {}),
                        'screw': ('McMaster 96817A204, 2 x 4 mm thread-forming for plastic'
                                  if insert_diameter is None else 'McMaster 92832A107, M2 x 4 button head'),
                        'washer': 'McMaster 93475A195, 2.2 ID x 5 OD x 0.2–0.4'},
            'screw_penetration_with_washer_mm':(2.6, 2.8),
            'pilot_diameter_depth_mm':p.pilot,
            'post_thread':'Formed in resin by 96817A204' if insert_diameter is None else 'M2 heat-set insert',
            'fit_temple_width_mm':2 * (mount_x - TEMPLE_CLEARANCE_PER_SIDE),
            'arm_inside_span_mm':2 * mount_x,
            'strap_anchor_outside_span_mm':2 * (mount_x + STRAP_EYE_DEPTH),
            'strap_width_mm':STRAP_NOMINAL_WIDTH,
            'strap_slot_throat_mm':STRAP_SLOT_THROAT,
            'strap_slots':{side:{'center':(sign * (mount_x + STRAP_EYE_DEPTH / 2),
                                           STRAP_SLOT_CENTER - 66, 0),
                                 'long_axis':'Z','clear_height':STRAP_SLOT_HEIGHT,'exit':'rearward'}
                           for side, sign in (('right', 1), ('left', -1))},
            'battery_retention':'Pocket walls capture the pouch under the PCB on its two existing screws',
            'notes':['For resin, check the cured pilot with a #52 drill and hand-drive the thread-forming screw.',
                     'PETG: heat-set McMaster 94459A767 flush in a 3.2 mm pilot; test the printed bore first.',
                     'Both arms share the same mirrored outline. The battery pocket and PCB posts are on the right.',
                     'USB-C,SW1/SW2,D1,TP1/TP2/TP3 and SH connectors remain exposed.',
                     'Pilot fit and thread hold require a printer/material coupon before final fabrication.']}


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


def strap_coupon(frame, mount_x):
    """Crop the actual eye from the finished frame, including its edge radii."""
    clip = place(_box(-5, -15, -1, 17, 30, 5), mount_x)
    return frame.intersect(clip)


def mount_coupon(frame, mount_x):
    """Crop a complete PCB post from the finished frame for a screw-fit trial."""
    u, v = PCB_NOTCHES[0]
    clip = place(_box(u - 4.5, v - 4.6, -.05, 10, 9.2, 7), mount_x)
    return frame.intersect(clip)
