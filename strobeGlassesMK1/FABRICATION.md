# MK1 fabrication notes

41.2 × 15.25 mm, two layers, 1.0 mm FR4, 1 oz copper. Black solder mask and white silkscreen suit the artwork.

The two R1.2 mm routed edge notches seat M2 screws. Use heads no larger than Ø5 mm. Copper clears R2.65 mm and artwork R2.75 mm around each axis. The frame must capture/support the board; check actual screws, washers, connector access and wire bend clearance during mechanical design.

Project settings and `.kicad_dru` carry the manufacturing limits: 0.15 mm track/clearance, 0.25 mm copper to routed edge, 0.60/0.30 mm vias, 0.18 mm PTH annular ring and 0.28 mm PTH hole-to-copper clearance. Existing tracks are 0.20/0.40/0.50 mm. Mask expansion is zero, minimum web 0.13 mm; silk text is at least 1.0 mm with 0.15 mm strokes. Filled-polygon DRC does not certify every fine artwork feature.

Charge with SW1 OFF. Battery J2 expects a protected 1S LiPo, pin 1 positive and pin 2 ground. The [BOM](../hardware-library/BOM.md) includes matching battery/cable options. Programming uses TP1 UPDI, TP2 VCC and TP3 GND.

[Independent hardware review](../hardware-library/BOARD_REVIEW.md) · [JLCPCB capabilities](https://jlcpcb.com/capabilities/Capabilities)
