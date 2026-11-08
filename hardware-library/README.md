# Hardware library

Local KiCad symbols, footprints and STEP models used by the MK1 board. The project library tables use relative paths, so the design opens with this folder beside `strobeGlassesMK1/`.

- [BOM and ordering notes](BOM.md)
- [One-board DigiKey CSV](digikey-bom.csv), [with spares](digikey-bom-with-spares.csv), [wiring](digikey-wiring.csv)
- [Independent hardware review](BOARD_REVIEW.md)

J2/J3/J4 use JST-SH 1 mm headers. Battery J2 is pin 1 positive, pin 2 ground; J3/J4 carry the independently driven eye electrodes. Check cable polarity. The BOM includes a protected 40 mAh battery with a matching SH plug and an adapter option for the on-hand PH battery.

Resistors and small ceramic capacitors are 0603 with hand-solder pads. C1/C2 are polarized KEMET A-case tantalums. The slide-switch model includes its nominal actuator sweep. Sources and KiCad asset licenses are in [sources](sources/PROVENANCE.md).
