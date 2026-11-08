# Order BOM

For **one fully populated PCB**: 23 purchased components, 15 order lines. TP1/TP2/TP3 are copper test pads and require no purchased parts. D1/R7 are included for the charge indicator.

- [DigiKey import: exact one-board quantities](digikey-bom.csv)
- [DigiKey import: one board with hand-assembly spares](digikey-bom-with-spares.csv)
- [DigiKey import: SH wiring parts](digikey-wiring.csv)
- [Independent board review](BOARD_REVIEW.md)

Use DigiKey “Upload a List” and map the part-number, quantity and reference columns. Select cut tape, not Digi-Reel. The spare list orders two each of ICs/switches/USB, five SH headers, four tantalum capacitors, ten of each small passive and five LEDs. Batteries, lenses and programmer are separate below.

| Qty | Refs | Part / value | Order MPN (DigiKey link) | DigiKey number |
| ---: | --- | --- | --- | --- |
| 1 | U1 | ATtiny402 MCU; SOIC-8 | [ATTINY402-SSNR](https://www.digikey.com/en/products/detail/microchip-technology/ATTINY402-SSNR/9554946) | ATTINY402-SSNRCT-ND |
| 1 | U2 | 4.20 V LiPo charger; SOT-23-5 | [MCP73831T-2ACI/OT](https://www.digikey.com/en/products/detail/microchip-technology/MCP73831T-2ACI-OT/964301) | MCP73831T-2ACI/OTCT-ND |
| 1 | J1 | 6-contact power-only USB-C; exact blank-suffix variant | [USB4125-GF-A](https://www.digikey.com/en/products/detail/gct/USB4125-GF-A/13547388) | 2073-USB4125-GF-ACT-ND |
| 3 | J2, J3, J4 | 2-pin JST-SH 1 mm right-angle headers | [SM02B-SRSS-TB](https://www.digikey.com/en/products/detail/jst-sales-america-inc/SM02B-SRSS-TB/926708) | 455-SM02B-SRSS-TBCT-ND |
| 1 | SW1 | Hard power slide switch | [SLW-662712-15A-SMT-TR](https://www.digikey.com/en/products/detail/same-sky-formerly-cui-devices/SLW-662712-15A-SMT-TR/29706052) | 2223-SLW-662712-15A-SMT-TRCT-ND |
| 1 | SW2 | Side-actuated preset button | [B3U-3000P](https://www.digikey.com/en/products/detail/omron-electronics-inc-emc-div/B3U-3000P/1534340) | SW1022CT-ND |
| 2 | C1, C2 | 6.8 uF 16 V tantalum; KEMET A-case; polarized | [T491A685K016AT](https://www.digikey.com/en/products/detail/kemet/T491A685K016AT/3759249) | 399-10132-1-ND |
| 1 | C3 | 100 nF 50 V X7R; 0603 | [C1608X7R1H104K080AA](https://www.digikey.com/en/products/detail/tdk/C1608X7R1H104K080AA/513811) | 445-1314-1-ND |
| 1 | C4 | 1 uF 10 V X5R; 0603 | [CL10A105KP8NNNC](https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL10A105KP8NNNC/3886840) | 1276-1182-1-ND |
| 2 | R1, R2 | 5.1 kohm 1% 0.125 W; 0603; USB CC pull-downs | [CRCW06035K10FKEA](https://www.digikey.com/en/products/detail/vishay-dale/CRCW06035K10FKEA/1174748) | 541-5.10KHCT-ND |
| 1 | R3 | 62 kohm 1% 0.1 W; 0603; ~16.1 mA charge setting | [RC0603FR-0762KL](https://www.digikey.com/en/products/detail/yageo/RC0603FR-0762KL/730283) | 311-62.0KHRCT-ND |
| 4 | R4, R8, R9, R10 | 2.2 kohm 1% 0.1 W; 0603; four LCD series resistors | [RC0603FR-072K2L](https://www.digikey.com/en/products/detail/yageo/RC0603FR-072K2L/727016) | 311-2.20KHRCT-ND |
| 2 | R5, R6 | 1 Mohm 1% 0.1 W; 0603; eye bleeders | [RC0603FR-071ML](https://www.digikey.com/en/products/detail/yageo/RC0603FR-071ML/729791) | 311-1.00MHRCT-ND |
| 1 | R7 | 6.2 kohm 1% 0.125 W; 0603; charge LED resistor | [CRCW06036K20FKEA](https://www.digikey.com/en/products/detail/vishay-dale/CRCW06036K20FKEA/1174759) | 541-6.20KHCT-ND |
| 1 | D1 | Orange LED; 0603; pad 1 cathode | [LTST-C190KFKT](https://www.digikey.com/en/products/detail/liteon/LTST-C190KFKT/386813) | 160-1434-1-ND |

**R7 substitution:** the selected Yageo RC0603FR-076K2L showed zero stock. The order files use Vishay CRCW06036K20FKEA, an equivalent 6.2 kohm, 1%, 0603 part with a higher 0.125 W rating. CAD selection is unchanged. Omit both R7 and D1 if you do not want a charge indicator.

All order lines above showed stock during the 2026-11-08 US DigiKey check. The exact one-board PCB parts total is about **$7.41** at the displayed one-piece prices, before shipping/tax/tariffs. Quantity discounts may lower it. Stock and checkout prices can change.

## Wiring and offboard items

| Qty | Item | MPN / DigiKey link | DigiKey number | When needed |
| ---: | --- | --- | --- | --- |
| 3 | JST-SH 2-pin cable housings | [SHR-02V-S-B](https://www.digikey.com/en/products/detail/jst-sales-america-inc/SHR-02V-S-B/759866) | 455-1377-ND | One per cable; two for eyes, plus battery adapter if reusing the PH pack. One is spare if buying the factory-SH battery. |
| 6 | Black 28 AWG precrimped wires, 152.4 mm, socket at both ends | [ASSHSSH28K152](https://www.digikey.com/en/products/detail/jst-sales-america-inc/ASSHSSH28K152/6009452) | 455-3076-ND | Lets you keep long leads for three pigtails. Cut near one end or split into shorter leads; three assemblies suffice if halved. Mark polarity clearly. |
| 1 optional | PH male pigtail for on-hand Adafruit battery | [Adafruit 3814](https://www.digikey.com/en/products/detail/adafruit-industries-llc/3814/9380221) | 1528-2617-ND | Splice to an SH pigtail to adapt the existing PH battery without changing its factory lead. Not needed with the SparkFun 40 mAh pack. |
| 1 if needed | UPDI programmer, cable included | [Adafruit 5879](https://www.digikey.com/en/products/detail/adafruit-industries-llc/5879/22596413) | 1528-5879-ND | If you do not already own a suitable UPDI programmer. Temporarily wire to TP1/TP2/TP3. |
| 4 total | Small LCD light valves | [Adafruit 3627](https://www.digikey.com/en/products/detail/adafruit-industries-llc/3627/8119807) | 1528-2516-ND | Two stacked, electrically parallel per eye. Buy only any shortfall from the valves already on hand. |

## Battery choice

Use the protected Adafruit/PKCELL 105 mAh pack already on hand for first bring-up, or try **[SparkFun 25270, 40 mAh](https://www.digikey.com/en/products/detail/sparkfun-electronics/25270/22606859)** / **1568-25270-ND** for the smaller build. The latter showed 267 in stock at $7.39. The finished protected pack is at most 22 × 11.5 × 3.5 mm, and its datasheet specifies SHR-02V-S-B with pin 1 red(+)/pin 2 black(-), matching J2 directly.

The 40 mAh pack specifies 8 mA standard charge and 20 mA maximum. This board is ~16.1 mA nominal, so it is below the maximum, with margin in the checked datasheet corners. Its taper endpoint differs from the charger; measure usable capacity/current on the final board before promising runtime. Keep R3 = 62 kΩ: arbitrarily increasing RPROG past 67 kΩ is outside the MCP73831 specified range and approaches shutdown detection.

Battery size can shrink now without changing the PCB, because only its connector is modeled. Keep enclosure clearance for the entire protected pack, its lead and the connector. Confirm actual cable polarity before connection. Measure the final ATtiny board current before choosing the final capacity.

[40 mAh pack specification](https://cdn.sparkfun.com/assets/4/f/c/6/3/SPE-DTP301120SH-3.7V-40mah-En-1.0V.pdf) · [SparkFun product](https://www.sparkfun.com/polymer-lithium-ion-battery-40mah-jst-sh.html)

## First-board conditions

- Charge with SW1 OFF; the charger has no load sharing. Use a protected 1S LiPo (3.7 V nominal, 4.2 V full).
- Program a conservative 5 MHz or slower ATtiny application, with balanced positive/negative LCD drive, clear-on-reset, button pull-up/debounce and brownout/low-battery handling.
- For UPDI Friend bring-up: SW1 OFF, Friend at 3.3 V, PWR to TP2, GND to TP3 and UPDI to TP1. Avoid tying its power output to a battery-driven rail.
- Check actual charging current, UPDI operation, lens voltage/contrast and board battery current on the assembled prototype. Mechanical fit follows; no PCB change is currently required by the review.
