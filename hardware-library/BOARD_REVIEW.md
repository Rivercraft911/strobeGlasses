# Independent board audit

Reviewed 2026-11-08. Read-only audit of the current schematic, routed board, fabrication rules, selected local parts and critical manufacturer drawings. No design, library, firmware or Git changes were made.

**Verdict: reasonable to order parts for a first assembled prototype. No hardware respin blocker was found.** This is an engineering review, not proof of the assembled hardware or optical performance. ATtiny firmware and a short first-board bring-up remain necessary.

## Fresh automated checks

- ERC: **0 violations** (errors and warnings included).
- Filled-zone DRC: **0 violations, 0 unconnected items, 0 schematic parity issues**.
- No board DRC exclusions. Existing ignored categories are missing courtyards, track centering, tuning profiles and footprint-filter/type checks; electrical clearance, shorts, net connectivity, library matching, soldermask, text and thermal checks remain active.
- Art minimum features are not certified by filled-polygon DRC; this affects appearance rather than electrical operation.

Evidence: fresh `erc.json`, `drc.json`, and independently exported `netlist.xml` are retained locally in `strobeGlassesMK1/build/order-review/audit/`.

## Findings and operating conditions

### P2: Preserve the intended charging and programming power arrangements

The board has a battery charger, not a power-path controller. **Charge with SW1 OFF.** With SW1 ON, operating current is included in the charger's measured battery current and can delay termination. The protected pack is essential: there is no separate PCB battery-protection circuit or reverse-polarity protection.

TP2 is correctly labeled **VCC** and is on **VBATT_SW**, not a regulated 3.3 V rail. For programming, use either battery power with a voltage-compatible, target-sensing UPDI interface, or SW1 OFF and a suitable external target supply on TP2/TP3. Do not tie a programmer's fixed 3.3/5 V power output to the battery-switched rail while SW1 is ON. TP1 is dedicated UPDI, not ordinary ISP/SWD. With the proposed UPDI Friend, the simplest first-board setup is SW1 OFF and the Friend set to 3.3 V powering TP2/TP3, so its logic and the isolated MCU supply agree.

### P2: Firmware must retain clock and LCD-drive constraints

The ATtiny's supply range covers a 1S LiPo. A 20 MHz build is inappropriate across this battery's discharge range; 20 MHz requires 4.5 V. A **5 MHz or slower CPU** is a simple conservative choice covering the chip's low-voltage range. Ten MHz is valid above the 2.7 V operating corner, with the datasheet's BOD qualifications.

Both eye pairs must receive balanced positive/negative drive, with both electrodes LOW for clear. Preserve equal polarity duration when changing presets or stopping, keep UPDI enabled, configure the mode-button pull-up, and debounce it. Configure brownout detection and low-battery behavior; watchdog/reset recovery should return the eyes to clear. The repository currently has the ESP32 bench sketch, not a finished ATtiny preset-button application.

### P2: Confirm the assembled cables, even when the housing fits

J2 is JST-SH 1 mm, pin 1 positive and pin 2 ground. The on-hand Adafruit/PKCELL pack has a JST-PH plug and needs the correct adapter. J3/J4 use the same SH header for electrode A/B, so identify battery versus eye cables clearly. The eye electrodes themselves have no permanent polarity. Check battery-cable continuity/polarity before plugging it into J2.

### P3: Mechanical fit still belongs to the enclosure pass

The R1.2 edge seats are routed notches, not captive holes. Copper is excluded within R2.65 of each screw axis; heads must be at most 5 mm diameter, and the frame must capture/support the PCB. Nominal adjacent switch bodies clear the head envelopes. Purchased screw/washer tolerances, plug insertion, switch access, wire bend radius and glass strain relief still require a physical enclosure fit check.

The prototype has four fragile glass valves, two stacked per eye; shrinking the battery does not change those lens dimensions.

### P3: Benign switch terminal-number convention

Omron's top-view diagram labels the two B3U-3000P terminals left2/right1; the local footprint labels them left1/right2. Because this exact part is a passive two-terminal normally-open switch, the reversal is electrically equivalent and does not prevent operation. Land geometry, side actuation and the no-boss/no-ground-terminal variant are correct. This is a documentation convention to tidy if desired, not an order blocker.

## Independent circuit trace

| Function | Verified connection / assessment |
|---|---|
| USB input | J1 A9/B9 → VBUS; A12/B12 and all shell tabs → GND. CC1 and CC2 each have their own 5.1 kΩ resistor to ground. Power-only USB-C; no PD request and no data connection. |
| Charger | U2 SOT-23 pins 1 STAT,2 GND,3 VBATT,4 VBUS,5 PROG. R3=62 kΩ gives approximately 16.1 mA, inside the manufacturer's2–67 kΩ programming range. C1/C2=6.8 µF, each above the recommended 4.7 µF. |
| Charge indicator | VBUS → R7 → D1 anode; D1 cathode → STAT. Correct active-low arrangement, approximately 0.4–0.5 mA during charge. It is not a battery-fed runtime LED. |
| Hard power | J2+ and charger output join VBATT; SW1 pin 2 is common, pin 1 feeds VBATT_SW, pin3 is unused. At the board's 180° rotation, the rightward ON marking agrees with the selected throw. |
| MCU | U1 pin 1 VCC,8 GND,6 PA0/UPDI,7 PA3 button. Left eye: PA1/pin 4 through R4 and PA2/pin 5 through R8. Right eye: PA6/pin 2 through R9 and PA7/pin3 through R10. Pinout matches the SOIC-8 device. |
| LCD branches | Each electrode has2.2 kΩ; R5/R6 are 1 MΩ across the glass side of the series pairs. Each eye connector feeds its two parallel valves. No permanent ground electrode or external H-bridge is required. |
| Decoupling | C3 = 100 nF plus C4 = 1 µF on VBATT_SW. C3 has a solid ground connection and an explicit short connection to a nearby ground via. Both ground layers are filled and connected. |

At 4.2 V, initial charging/short current through a resistor pair is at most about 0.95 mA. A full polarity reversal has at most about 1.91 mA initial current, because the initial capacitor voltage opposes the new drive. Those currents are comfortably below the ordinary GPIO's drive-test currents. The 2.2 kΩ resistors dominate output resistance and limit fault current; they are not merely power-saving parts.

The 1 MΩ bleeder causes only 0.44% static amplitude loss and at most 4.2 µA per dark eye. Its power-off discharge time depends on the actual combined valve capacitance. The manufacturer does not publish enough capacitance/optical-transition data to prove the highest usable carrier frequency. Scope the assembled eye pair at high and low battery voltage and compare optical clearing/darkening; an excessively high carrier can attenuate voltage through the series RC network.

Adafruit recommends at most 5 V and AC drive to avoid sustained DC bias. The1S battery stays below that limit. User bench observations at 3.3/3.7 V support this architecture, but useful darkness near battery depletion remains a measurement, not a DRC result.

## Package, polarity and fabrication checks

- **USB4125-GF-A:** compared against current official GCT drawing. Six signal pads,0.60×1.20 mm plated slots and 1.10×1.70 mm shell lands match. Blank suffix has1 mm shell stakes; do not silently order the0190 variant. Nominal 1 mm PCB is consistent with the selected stake variant.
- **SLW-662712-15A-SMT-TR:** manufacturer rev 1.0 p2 matched: signal lands 0.8×1.5 mm at 3.0/1.5 mm pitch; mechanical centers 7.3×2.2 mm; Ø0.9 locating holes 3.0 mm apart. Pin2 common confirmed. Body/actuator envelope is simplified project CAD, not a tolerance-certified assembly model.
- **B3U-3000P:** correct two-terminal side-actuated, no-ground/no-boss variant. Local 0.9×1.7 mm pads give 0.1 mm more lateral solder margin than the nominal drawing, an acceptable stock-footprint allowance.
- **JST-SH:** correct SM02B-SRSS-TB side-entry header, not JST-PH. Signal pads, hold-downs and mating SHR-02V-S-B family match.
- **Passives and ICs:** SOIC-8, SOT-23-5 and 0603 geometries agree with selected packages. C1/C2 are polarized A-case tantalums; positive stripes go to pad1. D1 pad1 is cathode and its board marking is on that end. All selected resistor powers and capacitor voltage ratings have ample margin at this circuit's currents/voltages.
- **Routing:** 124 segments at 0.20/0.40/0.50 mm and 15 vias at 0.60/0.30 mm. These are ample for approximately 16 mA charging and the small MCU/LCD load. Charger dissipation is on the order of 40 mW at low battery, rather than a high-heat load.

## Smaller battery and R7 purchase substitution

**SparkFun 25270 / DTP301120SH 40 mAh** is electrically compatible with the present charger, subject to normal current verification on the assembled board. The pack specification allows 20 mA continuous charge; 16.1 mA nominal is below it. Scaling the charger's published 67 kΩ/16.5 mA maximum corner with a 1% low 62 kΩ resistor gives approximately 18.0 mA, still below 20 mA within the stated charger test conditions. This is a conservative estimate, not an independent complete tolerance model.

The battery's p9 drawing explicitly specifies **JST-SHR-02V-S-B, P1 red(+), P2 black(-)**, matching J2. Finished pack maximum is **22×11.5×3.5 mm**, including protection. Its standard charge is 8 mA, maximum 20 mA; protected undervoltage cutoff is approximately 2.4 V. Use a sensible firmware low-battery stop for optical performance and the conservative CPU clock above. The battery's capacity test uses a 0.4 mA taper endpoint; selected charger AC option terminates at about 1.2 mA nominal, so do not promise every nominal mAh without measuring usable capacity.

Do not reduce charge current by choosing arbitrarily large RPROG: above 67 kΩ it is outside the specified range and 70–200 kΩ overlaps shutdown detection. Cells with a lower permissible charge current need a suitable low-current charging solution.

**R7 substitute CRCW06036K20FKEA** is a valid drop-in 6.2 kΩ 0603 ±1% part with 0.125 W rating. Actual dissipation is only around 1.5 mW. Record the purchasing substitution; no electrical/layout change is needed.

## Primary references

- [Microchip MCP73831/2 datasheet](https://ww1.microchip.com/downloads/en/DeviceDoc/MCP73831-Family-Data-Sheet-DS20001984H.pdf): pin table, current-programming range, capacitor requirements and AC option.
- [Microchip ATtiny202/204/402/404/406 datasheet](https://ww1.microchip.com/downloads/aemDocuments/documents/MCU08/ProductDocuments/DataSheets/ATtiny202-204-402-404-406-DataSheet-DS40002318A.pdf): pinout and electrical sections33.3,33.10.
- [GCT official USB4125 drawing](https://gct.co/files/drawings/usb4125.pdf), revisionA6.
- [Same Sky slide-switch drawing](https://www.sameskydevices.com/product/resource/slw-662712-15a-smt-tr.pdf), revision1.0, p2; locally retained manufacturer PDF inspected visually because the web fetch returned403.
- [Omron B3U manufacturer drawing](https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3u.pdf), p3.
- [JST SH manufacturer drawing](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf).
- [Adafruit 3627 product specification](https://www.adafruit.com/product/3627) and [manufacturer glass drawing](https://cdn-shop.adafruit.com/product-files/3627/C10669_new_edition_GDC1260AA.pdf).
- [PKCELL/Adafruit 1570 protected 105 mAh pack specification](https://cdn-shop.adafruit.com/product-files/1570/1570datasheet.pdf).
- [SparkFun supplied DTP301120SH 40 mAh pack specification](https://cdn.sparkfun.com/assets/4/f/c/6/3/SPE-DTP301120SH-3.7V-40mah-En-1.0V.pdf), pp4,7,9.

Only prototype bring-up can confirm assembled solder joints, charging current, UPDI operation, final firmware timing, actual battery life and optical performance. Mechanical design can follow without a presently identified electrical respin requirement.
