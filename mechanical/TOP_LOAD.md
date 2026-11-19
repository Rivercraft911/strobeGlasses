# MK1 top-loading frame

One Adafruit 3627 slides down into each fixed rim. A single cover drops onto
the outside of the brow, in front of the upright pins. Four short stops on its
underside catch the glass corners. Across both halves, the cover stays at
least 1.15 mm forward of the fixed rear rim plane in CAD. The cable guides
are part of the frame.

![Overhead view of the cover in front of the pins, beside the exploded assembly](top-load-brow.png)

## Fit and assemble

1. Print one matched frame and cover. For a PETG trial, keep the glass slots
   vertical and keep support contacts out of the slots, pilots and wire guides.
   Clean up the print and try each loose pane before fitting the wires.
   For Tough 2000 Resin V2, flush the slots and pilots before curing.
2. Lower each pane straight down, metal pins up. The 2.20 mm slot leaves
   0.37 mm total front-to-back clearance for the measured 1.83 mm glass.
   The side lanes clear the fill tab and the cutout clears the pin roots.
   [Panel drawing](https://cdn-shop.adafruit.com/product-files/3627/C10669_new_edition_GDC1260AA.pdf)
3. Sleeve the solder joints and bend the flexible wires toward the fixed
   trough. The metal pins stay straight. Run the left pair across the
   bridge and both pairs through the right shoulder. Thread the loose crimps
   before clicking them into the two-pin housings. J3 is left and J4 is right.
4. With the wires in their guides, lower the cover vertically onto the two
   outside posts. The long edge passes in front of both pin pairs. It should
   seat by hand. Fit two McMaster 96817A204 thread-forming screws (2 × 4 mm,
   T6/IP6). The heads bear on the cover and posts. [Cap screws](https://www.mcmaster.com/96817A204/)
5. Invert the assembly over the bench to check that the panes stay captured.
   With power off, try the frame with the strap lightly tensioned to check
   forehead and lash clearance. The frame uses no face foam.

The matched STLs sliced in OrcaSlicer with generic PETG, a 0.4 mm nozzle,
0.20 mm layers, three walls and build-plate supports. Physical fit still
needs checking on the printed pair.

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
