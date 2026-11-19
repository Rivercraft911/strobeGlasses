# MK1 parts and assembly

Import the [one-board DigiKey CSV](digikey-bom.csv) with “Upload a List”
and scale the quantities for your board count. TP1–TP3 are bare test pads.

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
| 1 | R7 | 6.2 kΩ 1%; 0603; charge LED resistor | [CRCW06036K20FKEA](https://www.digikey.com/en/products/detail/vishay-dale/CRCW06036K20FKEA/1174759) | 541-6.20KHCT-ND |
| 1 | D1 | Orange LED; 0603; pad 1 cathode | [LTST-C190KFKT](https://www.digikey.com/en/products/detail/liteon/LTST-C190KFKT/386813) | 160-1434-1-ND |

R1/R2 can also use Panasonic ERJ-3EKF5101V (P5.10KHCT-ND). The R7 listed
above replaces the schematic's Yageo 6.2 kΩ part. D1 and R7 can both be left
off if you skip the charge indicator. Match the positive stripe on C1/C2
to pad 1. D1 pad 1 is the cathode.

| Per pair of glasses | Part | DigiKey number |
| ---: | --- | --- |
| 2 | [Adafruit 3627 light valves](https://www.digikey.com/en/products/detail/adafruit-industries-llc/3627/8119807) | 1528-2516-ND |
| 2 | [JST-SH 2-pin cable housings](https://www.digikey.com/en/products/detail/jst-sales-america-inc/SHR-02V-S-B/759866) | 455-1377-ND |
| 2 | [JST ASSHSSH28K305 double-ended 305 mm precrimped leads](https://www.digikey.com/en/products/detail/jst-sales-america-inc/ASSHSSH28K305/6009453) | 455-3077-ND |
| 1 | [SparkFun protected 40 mAh LiPo with JST-SH](https://www.digikey.com/en/products/detail/sparkfun-electronics/25270/22606859) | 1568-25270-ND |

Wire one valve per eye. J3 drives the left and J4 the right. One 305 mm
lead supplies one long and one short conductor. [Frame and harness assembly](../mechanical/TOP_LOAD.md)

For a protected pack with a JST-PH plug, make an adapter with one
extra SH housing, two SH contacts and an [Adafruit 3814 PH pigtail](https://www.adafruit.com/product/3814).
Check J2 polarity before plugging in. Pin 1 is positive and pin 2 is ground.

Charge with SW1 off. R3 sets about 16 mA. Use a protected 4.2 V full-charge
LiPo rated for that current. The SparkFun pack allows up to 20 mA and measures
at most 22 × 11.5 × 3.5 mm. [Battery datasheet](https://cdn.sparkfun.com/assets/4/f/c/6/3/SPE-DTP301120SH-3.7V-40mah-En-1.0V.pdf)

The board is 41.2 × 15.25 mm, two layers, 1.0 mm FR4 and 1 oz copper.
Black solder mask and white silkscreen match the render. The M2 edge notches
take screw heads up to 5 mm across. Support the board in the frame so the
screws can capture it.

One [UPDI Friend](https://www.digikey.com/en/products/detail/adafruit-industries-llc/5879/22596413)
can flash every board. See the
[firmware and flashing instructions](../firmware/strobe_glasses/README.md).
