# MK1 Slim

Two shallow 20° lens carriers join at a rounded nose arch. The shoulders
sweep into the temples. A shared retainer snaps into the shoulders.
The blue rings in the CAD views represent the cut black foam pads. The
PCB closes the battery pocket with its two existing M2 screws.

## Print and assemble

1. Print the coupons in `snap-test/` and `strap-test/` with the same resin,
   orientation and cure you plan to use for the frame. Test that the snap
   holds and releases, and thread your actual band. Press the snap spring
   toward the lens to release it.
2. In the resin slicer, angle the frame and retainer so the openings and
   battery pocket drain. Keep supports off the glass seats, snap passages,
   insert bores and visible face. Tilt the lead exit downhill so the
   battery pocket drains through it. Inspect the ceilings of the strap
   slots and both terminal bays before printing.
   [Example tough black resin](https://www.resione.com/products/k-plus)
3. Load two Adafruit 3627 valves per eye from the rear along each lens
   carrier, front valve first. Match their optical orientation. Cut the
   perimeter spacers from 0.5 mm matte black insulating sheet using
   `valve-spacer-template.svg`.
   Two lower stops locate the front valve 1.5 mm higher. The cavity gives
   a maximum size panel 0.30 mm of clearance along each edge. Use soft
   perimeter shims sized to the actual stack to prevent rattle. Press the
   retainer straight forward into both latches. Squeeze the latches toward
   the lenses and pull the retainer straight back to remove it.
4. The shallow assembly uses terminals shortened to about 3.5 mm from
   the bend. Fit the short insulated solder joints in the top openings and
   route the flexible pigtails out along the brow. Connect each eye's two
   valves in parallel. Keep the joints off the skin-facing edge and cover
   the open cable passages with thin opaque tape after the wiring fits.
   [Valve drawing](https://cdn-shop.adafruit.com/product-files/3627/C10669_new_edition_GDC1260AA.pdf)
5. Glue the two brass inserts into the cured frame with a small amount of
   two-part epoxy on the outside of the inserts. Keep the threads clean
   and let the epoxy cure. Drop the battery into the pocket with its wires
   pointing toward the glasses. Route the lead through the front opening
   and under the board edge to J2. Tighten the two M2 screws through the
   existing PCB notches. The board should seat on both posts and capture
   the pouch with room above it. Check the fit and USB-C access on the
   first print.

The 22.6 × 12.1 mm pocket fits the protected SparkFun 25270 40 mAh pack up to
22 × 11.5 × 3.5 mm. The posts leave about 1.5 mm above a maximum thickness
pack. The free lead is 21.5 ± 3 mm from the pack to the back
of the plug. J2 pin 1 is battery positive. [Battery drawing](https://cdn.sparkfun.com/assets/4/f/c/6/3/SPE-DTP301120SH-3.7V-40mah-En-1.0V.pdf)

## Make the light seal and strap

Print both foam templates at 100% and check their 20 mm rulers. Cut the
base pads from `foam-template.svg` and the face pads from
`foam-face-template.svg`, using 1/8″ black adhesive-backed neoprene for
both. The notched base pads go on the retainer with the notches up. Start
the unpowered fit check with both layers. The wider opening in the face
pad leaves room around the lids and bridges the base pad's wire notch.
Keep wires flush in their channels and trim the pad locally if needed.

With the strap lightly tensioned, blink normally and look up and down.
Check lash clearance and that the foam lands evenly around the brow and
cheeks. Use one layer if it clears your lashes and seals comfortably.
If you can see outside light near the cheeks or temples, cut local strips
with `foam-shim-template.svg`. Add one layer where needed and taper the
ends into the face pad. Keep each strip backed by the pad underneath.
Try the strips provisionally and check normal head movements before bonding.
The 126 mm temple measurement sets the fit target, and the straight inner
arms are 138 mm apart. The hard anchor tabs span 143 mm on the outside.

Use 3/4″ flat elastic in the 20.8 × 4.2 mm slots. Thread one end through,
fold a 25 mm return back, and bar-tack it to itself. On the other end,
run the elastic through a matching wide-mouth slider, through the second
printed slot once, and back through the slider. Start with about 650 mm of
elastic and leave a 50 mm adjustment tail while fitting. Try the doubled
elastic through the coupon and slider before cutting the other straps.
Keep the stitched fold outside the slot and clear of the USB-C plug.
Set light strap tension and use the pads to fill local gaps. Check for
even contact without pressure on the brow or nose.

## Small parts for five pairs

| Qty for five pairs | Part |
| ---: | --- |
| 10 | [CNC Kitchen M2 × 3 brass inserts, Ø3.6 mm outside](https://cnckitchenus.store/products/heat-set-insert-m2-x-3-100-pieces) |
| 10 | [CNC Kitchen M2 × 4 mm low-head screws](https://cnckitchenus.store/products/m2-screw-stainless-steel-aisi-304-low-head?variant=48314245677156) |
| 10 | [M2 washers for the PCB notches, Ø5 × 0.3 mm](https://cnckitchenus.store/products/stainless-steel-nuts-din934-kopie?variant=47400098758756) |
| 1 roll | [Airisoer 3/4″ black flat elastic, 12 yd](https://www.amazon.com/dp/B0CBYLZM5Q) |
| 5 | [Black wide-mouth 3/4″ three-bar sliders](https://www.strapworks.com/34-inch-plastic-slide-wide-mouth-black) |
| 1 pack | [Storystore 1/8″ black adhesive-backed neoprene, five sheets](https://www.amazon.com/dp/B08P1XQMQH) |

The resin pilot is Ø3.8 × 4.0 mm with a short entry chamfer. Check your
inserts and the printed bore before gluing. Set them flush. PETG uses
the insert maker's Ø3.2 mm heat-set pilot. [Insert dimensions](https://cnckitchen.com/s/CNCKitchen_Heat-Set-Insert-Dimensions-and-Design-Guidelines.pdf)

## CAD and print checks

- Measured perpendicular to each LCD, the rigid optical stack is 7.25 mm.
  The retainer plate is 1.05 mm thick, with 1.25 mm at the snap beams.
  One foam layer brings local depth to 10.43 mm and two to 13.60 mm before
  compression.
- At 35% foam compression, the contact plane sits 3.46 mm behind the rear
  glass with one layer and 5.53 mm behind it with two. The wearer’s cornea
  and lashes sit at a different depth from that plane. Check actual fit
  with the glasses unpowered.
- The front seat is 1.10 mm thick. The snap channel opens inward near its
  entry and uses an outer catch shoulder. Each spring beam is 1.30 mm wide.
  The nose relief has a 0.50 mm edge radius at the bridge.
- The maximum size panes have 0.30 mm of side clearance, with 0.25 mm
  available at the front seat and 0.35 mm at the rear for soft shims. Check
  those shims against the actual panel thickness before seating the retainer.
- The snap check moves both hooks through withdrawal with 0.60 mm inward
  travel. The cured coupon checks actual flex and print tolerance.
- Straight through, the 32 × 28.3 mm rounded apertures clear both foam pads
  and the retainer. The wearer view shows their alignment.
- On the unscaled NIOSH Small headform, the wrap reduced the projected
  rear glass-to-headform gap at eye height from about 21 to 16.5 mm at the
  aligned pose. The cheek and temple gaps call for local pad fitting.
  Check the real LCDs at 20° incidence and check comfort with the glasses
  unpowered. [NIOSH headforms](https://stacks.cdc.gov/view/cdc/223510)
- The strap slots leave 3.1 mm of material on each side along the band
  pull direction. A 19.05 mm wide elastic stack 3.6 mm thick passes with
  0.29 mm of minimum modeled clearance. The USB plug clears the modeled
  strap by 0.40 mm.
- The captive pack has 1.50 mm nominal clearance above it. Its lead exit
  opens down to the pocket floor so the uncapped part drains during printing.

## Rebuild the CAD

Use CadQuery 2.8 with `build_slim.py`. The PCB STEP uses the origin
`115.8x137.625mm` in KiCad. The included reference STEP is from the populated
MK1 board. Run the command from the extracted download folder.

```sh
python source/build_slim.py --pcb-step reference/mk1-pcb.step --output build
```

Pass `--foam-layers 1` to export the one-layer assembly.
Use `--wrap-degrees 0` for the flat comparison. For a repository checkout,
generate the populated board STEP from the project root with KiCad CLI.

```sh
mkdir -p mechanical/build/reference
kicad-cli pcb export step --force --user-origin 115.8x137.625mm \
  -o mechanical/build/reference/mk1-pcb.step strobeGlassesMK1/strobeGlassesMK1.kicad_pcb
python mechanical/build_slim.py
```
