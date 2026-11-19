# MK1 top-loading frame

The two prints are the frame and a narrow brow keeper. One Adafruit 3627
slides down into each fixed rim, pins up. Four short tabs on the keeper
capture the glass corners. The strip between them is 2.24 mm wide and
2.0 mm tall. The sculpted front ridge and both cable guides stay on the frame
when the keeper lifts off.

![Keeper raised above the fixed wire guides and upright terminals](top-load-brow.png)

## Fit and assemble

1. Print one frame and keeper in Tough 2000 Resin V2. Keep supports off the
   inside guide faces, keeper seats and screw pilots. Flush the slots and
   pilots before curing. Try one loose valve in each finished slot.
2. Lower the valves straight down to the bottom seats. The design slot is
   2.20 mm deep for the measured 1.83 mm glass, leaving 0.37 mm of total
   front-to-back play before print variation. The side lanes clear the
   seal tab all the way down. The central cutout extends below the pin roots
   and stays open above all four terminals. [Panel drawing](https://cdn-shop.adafruit.com/product-files/3627/C10669_new_edition_GDC1260AA.pdf)
3. Lay the keeper behind the pins and lower it onto its two locating posts.
   It should seat by hand. Fit two McMaster 96817A204 thread-forming screws
   (2 × 4 mm, T6/IP6), one at each end. Turn by hand until the heads seat.
   Each head bears on the keeper and its post. Remove the keeper if it
   rocks or if a pane needs force to enter. [Cap screws](https://www.mcmaster.com/96817A204/)
4. Sleeve the soldered terminals and leave the flexible wire free at each
   pin. Keep the pins upright and bend only the insulated leads forward.
   Route the left pair across the bridge and both pairs through the right
   shoulder guide. Thread the loose crimps through the guides before clicking
   them into the two-pin housings. Plug the left pair into J3 and the right
   into J4. Dress the wires on the fixed ridge, clear of the keeper’s lift path.
5. Check both panes stay captured with the frame inverted over the bench.
   Try it unpowered with the black strap lightly tensioned and check lash
   clearance. The frame uses no face foam.

The MK1 battery pocket, board posts and strap slots are carried over from
the first frame. Allow four 2 × 4 mm screws per pair of glasses, two for the
keeper and two for the PCB. [Battery, PCB and strap assembly](SLIM.md)

## Rebuild

Use CadQuery 2.8. The generator checks glass insertion, pin clearance, keeper
lift, wire routing and both exported meshes. Supply the populated MK1 board
with `--pcb-step /path/to/board.step` to include it and the battery in the
assembly and check their fit. The KiCad export origin is 115.8 × 137.625 mm.
The default output is `mechanical/build/mk1-top-load`. Use `--output` for another drive.

```sh
python mechanical/top_load.py
```
