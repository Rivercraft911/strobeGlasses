# MK1 Slim

The brow rolls over two flat, 20° lens bays and sweeps into the strap eyes.
The frame and shared snap-in retainer are the two required prints. An
optional center-brow accent can be printed separately in red or white. The
right arm carries the board over the battery. The shallow grooves above the
lenses can take a paint accent after printing.

## Print and assemble

1. Start with `lens-test/lens_bay.stl` and `lens-test/lens_retainer.stl`.
   These are cuts from the finished parts. Try two actual wired panels, a
   spacer and the latch in this single bay. Use the separate strap and
   insert coupons to check your elastic and brass inserts.
2. For PETG, the frame STL sits upright on two flat lands under the lenses.
   Start with a 0.4 mm nozzle, 0.20 mm layers, four walls, a 4 mm brim and
   removable supports under the arms and across the optical openings. Inspect
   the support preview around the clips and the wire exits. Block supports
   inside the two short wire passages. Try the shoulder guide coupon with
   a loose crimp contact before printing the full frame. For tough resin,
   tilt the parts with the battery lead exit downhill and put support marks
   away from the lens seats and the brow.
3. Cut and route the wires as described below before soldering the valves.
   Match each pair’s optical orientations.
   At each shortened front terminal, solder the pigtail and one jumper side by
   side, then sleeve the joint. Loop the jumper back to the matching rear
   terminal and sleeve that joint too. The four sleeves per eye fit a
   2.4 × 1.5 mm envelope, with 3.5 mm of terminal behind each bend. Try
   the soldered stack in the single-bay coupon. [Valve drawing](https://cdn-shop.adafruit.com/product-files/3627/C10669_new_edition_GDC1260AA.pdf)
4. From the wearer side, fit the two wired panes and the 0.50 mm perimeter
   spacer into each bay, terminals up. The front pane sits on two lower stops
   which stagger the solder joints by 2.0 mm. Cut the spacers using
   `valve-spacer-template.svg`. Fit soft edge shims for the actual stack.
   Feed the flexible leads up through the open brow notches and press the
   shared retainer forward at the outer edges until both hooks seat.
5. Heat-set two **McMaster 94459A767** M2 inserts flush in the PETG posts
   before installing the cell. The nominal pilot is Ø3.2 × 4.0 mm.
   For cured resin, test the Ø3.8 mm adhesive pilot against the actual knurl
   diameter and bond the inserts with epoxy. Use the insert coupon first.
   Drop the battery into its pocket, wires forward. Guide them below the
   board edge to J2. Fit one Ø5 mm washer under each M2 × 4 button head.
   Both screws seat the board on the posts and capture the cell.

### Route the harness

The left pair crosses the fixed brow to **J3**. The right pair follows the
shorter path to **J4**. Each plug’s pin 1 drives the same terminal on both
panes. Pin 2 drives both opposite terminals. Mark one of the black conductors
at each end before soldering. The assembly STEP colors each eye for visibility.

For one pair of glasses, cut **two 305 mm double-ended crimp leads**. From
each lead, save one 165 mm crimped end for the left and one 90 mm crimped end
for the right. Use the middle offcuts for the four same-terminal jumpers.
Starting at the PCB, feed all four **bare solder ends** through the molded
passage in the right shoulder. Feed the two longer ends through the passage
at the nose bridge and on to the left eye. Lay the rest into the open
channels, leave a service bend at each plug, then trim and solder. The
shallow routes take 0.8 mm insulated wire. Each short jumper has about
6.7 mm of wire between sleeves plus the stripped ends. [JST SH drawing](https://www.jst.com/wp-content/uploads/2021/01/eSH.pdf)

The two molded passages retain the harness with the brow bare. For a color
accent, print `optional/brow_accent.stl` and seat it between the lens bays.
Its underside leaves 0.15 mm over the mating rails. Apply narrow strips of
0.13 mm transfer tape to the clean rail tops, keeping the cable bed and
sleeves clear. The outer temple remains open for connector access.
[3M 9472LE transfer tape](https://multimedia.3m.com/mws/media/2366131O/3m-adhesive-transfer-tape-9472le.pdf)

To release the carrier, unplug J3 and J4 by their ears, pinch the two lands
inward about 0.9 mm and draw it straight back. For complete removal of a
wired valve assembly, peel off the optional accent, mark the pin order,
release the contacts from that plug housing and feed them back through
the guides one at a time.

The 22.6 × 12.1 mm pocket fits the protected SparkFun 25270 40 mAh pack up to
22 × 11.5 × 3.5 mm. The posts leave about 1.5 mm above a maximum thickness
pack. The free lead is 21.5 ± 3 mm from the pack to the back
of the plug. The two CAD routes are 17.1 and 18.2 mm. The longer route
leaves about 0.3 mm at the shortest specified lead length. Dry-fit the pack
and close the board only when the plug seats without tension. J2 pin 1 is battery positive. [Battery drawing](https://cdn.sparkfun.com/assets/4/f/c/6/3/SPE-DTP301120SH-3.7V-40mah-En-1.0V.pdf)

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
arms are 138 mm apart. The strap bars span about 143 mm on the outside.

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
| 10 | [McMaster 94459A767, brass M2 × 0.4 heat-set insert, 3.2 mm installed length, pack of 50](https://www.mcmaster.com/94459A767/) |
| 10 | [McMaster 92832A107, M2 × 4 mm Torx button head, pack of 50](https://www.mcmaster.com/92832A107/) |
| 10 | [McMaster 93475A195, M2 stainless washer, Ø5 × 0.2–0.4 mm, pack of 100](https://www.mcmaster.com/93475A195/) |
| 10 | [JST SHR-02V-S-B two-pin housings for J3 and J4](https://www.digikey.com/en/products/detail/jst-sales-america-inc/SHR-02V-S-B/759866) |
| 10 | [JST ASSHSSH28K305, 305 mm, 28 AWG, socket at each end](https://www.digikey.com/en/products/detail/jst-sales-america-inc/ASSHSSH28K305/6009453) |
| 1 roll | [Airisoer 3/4″ black flat elastic, 12 yd](https://www.amazon.com/dp/B0CBYLZM5Q) |
| 5 | [Strapworks PLH-SLD-034-WDM-BLK, 3/4″ wide-mouth sliders](https://www.strapworks.com/34-inch-plastic-slide-wide-mouth-black) |
| 1 pack | [Storystore FSSA01, 1/8″ adhesive neoprene, five 12 × 8″ sheets](https://www.amazon.com/dp/B08P1XQMQH) |

One pack of each McMaster part covers all five frames. With the 1.0 mm
finished PCB and the specified washer range, the screw enters the insert
2.6–2.8 mm. The centered washers clear the nearest front solder-mask
openings by at least 0.67 mm on MK1. The STEP shows a smooth insert core at the pilot diameter. Use
the coupon to check the actual knurls and the grip of the installed insert.
Buy 3.25 m of elastic if buying by length. Cut two base and two face pads per
frame. Keep the adhesive toward the retainer on the base and toward the base
on the face pad. [McMaster insert table](https://www.mcmaster.com/products/bushings/thread-size~m2/)

## CAD and print checks

- On the wrapped frame, sections through the molded cable passages measured
  at least 1.38 mm of roof and 1.57 mm of floor at the sampled wire lanes.
  The narrowest sampled roof-to-floor gap was 1.94 mm. Test a loose contact
  in the printed shoulder coupon to measure bridge sag on your printer.

- The front and rear design datums are 7.25 mm apart along the lens normal.
  The retainer plate is 1.05 mm thick, with 1.25 mm at the snap beams.
  One foam layer brings local depth to 10.43 mm and two to 13.60 mm before
  compression.
- At 35% foam compression, the contact plane sits 3.46 mm behind the rear
  glass with one layer and 5.53 mm behind it with two. The wearer’s cornea
  and lashes sit at a different depth from that plane. Check actual fit
  with the glasses unpowered.
- The 34.4 × 31.2 mm front bevel tapers to the 32 × 28.3 mm optical bore.
  The snap channel opens inward at its entry. The 1.30 mm wide spring
  beam has 0.30 mm nominal lateral clearance in the straight guide.
- The maximum size panes have 0.30 mm of side clearance, with 0.25 mm
  available at the front seat and 0.35 mm at the rear for soft shims. Check
  those shims against the actual panel thickness before seating the retainer.
- The snap check moves both hooks through withdrawal with 0.90 mm inward
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

Open `mk1-bare.step` for the assembled glasses. `mk1-slim.step` also
includes the optional accent as a separately selectable solid.
The two pieces in `print/` make the complete bare frame.

Use CadQuery 2.8 with `build_slim.py`. The PCB STEP uses the origin
`115.8x137.625mm` in KiCad. The included reference STEP is from the populated
MK1 board. Run the command from the extracted download folder.

```sh
python source/build_slim.py --pcb-step reference/mk1-pcb.step --insert-diameter 3.2 --output build
```

Check rear loading, terminal clearance, both hooks and access to the release
lands with `python source/check_lens_fit.py build`. Its lens sweep adds
0.15 mm at each edge of the maximum panel envelope. The released-hook
sweep adds 0.30 mm at each side and above and below. These are modeled
print-error allowances. Try the single-eye coupon on your machine.

The command above builds the PETG version. Use `--insert-diameter 3.8` for resin.
Pass `--foam-layers 1` to export the one-layer assembly.
Use `--wrap-degrees 0` for the flat comparison. For a repository checkout,
generate the populated board STEP from the project root with KiCad CLI.

```sh
mkdir -p mechanical/build/reference
kicad-cli pcb export step --force --user-origin 115.8x137.625mm \
  -o mechanical/build/reference/mk1-pcb.step strobeGlassesMK1/strobeGlassesMK1.kicad_pcb
python mechanical/build_slim.py
```
