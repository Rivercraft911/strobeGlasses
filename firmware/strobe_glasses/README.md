# MK1 firmware

Power on with both lenses clear. Tap to resume the last preset. The first boot
uses Light. Both eyes strobe together.

| State | Tap | Hold for 0.8 s |
| --- | --- | --- |
| Clear | Resume selected preset | Preview and edit its FPS |
| Strobing | Cycle Light → Balanced → Heavy → Custom | Clear both lenses |
| Editing FPS | Step to the next rate | Move to duty |
| Editing duty | Step to the next dark percentage | Save to Custom and resume |

Light is 6 fps at 40% dark, Balanced is 5 fps at 50%, and Heavy is 4 fps at
60%. Custom starts at 5 fps and 50%. FPS steps through 2, 4, 5, 6, 8, 10, 15,
and 20. Duty steps from 20% to 80% in steps of 10 percentage points. Both
lists wrap around. A brief clear pause marks the switch to duty and the save.
Power off during an edit to discard the draft. The last selected preset and
saved Custom values survive power cycles.

The timer splits every dark window into balanced AC pairs near 100 Hz.
Stopping finishes the current pair and drives both leads low. FPS and duty
describe the electrical timing. Check optical contrast and clearing on the
assembled valve stacks.

## Flash with UPDI

Open `strobe_glasses.ino` in Arduino IDE with [megaTinyCore](https://github.com/SpenceKonde/megaTinyCore/blob/master/Installation.md)
installed. Use the ATtiny 412/402/212/202 board family, chip **ATtiny402**,
clock **5 MHz internal**, and leave the millis timer at **Enabled (default timer)**.

1. Turn SW1 off and unplug the glasses' charging cable. Set the UPDI Friend
   to 3.3 V, then connect **PWR → TP2**, **GND → TP3**, and **UPDI → TP1**.
2. Select the programmer's serial port and **SerialUPDI – SLOW: 57600 baud**.
3. On initial setup, select **BOD 2.6 V**, **Enabled/Enabled**, and
   **EEPROM retained**. Run **Burn Bootloader** to apply those fuses with the
   standard ATtiny402 board selection.
4. Use **Sketch → Upload Using Programmer**. The programmer can power the
   first bench check below. Disconnect it before switching to battery power.

[UPDI Friend guide](https://learn.adafruit.com/adafruit-updi-friend?view=all)

To compile from the repository root with megaTinyCore 2.6.11 installed:

```sh
arduino-cli compile --fqbn megaTinyCore:megaavr:atxy2:chip=402,clock=5internal,bodvoltage=2v6,bodmode=enabled,eesave=enable --build-path firmware/strobe_glasses/build/avr firmware/strobe_glasses
```

## First board check

1. Leave the battery and lenses disconnected. With power off, check TP2 (VCC)
   and TP3 (GND) for a solder short. Flash over UPDI, then leave the 3.3 V
   programmer attached to power the board.
2. Put one scope tip on each pin of J3. Connect both probe grounds to TP3
   and display CH1 − CH2. At startup both pins should read 0 V relative to
   TP3. On a fresh chip, tap SW2 twice to reach Balanced.
3. Expect a 200 ms frame on Balanced. For 100 ms the differential waveform
   alternates between about +3.3 V and −3.3 V every 5 ms. Both pins then
   stay low for 100 ms. Check J4 the same way. Hold SW2 for 0.8 s and
   confirm both connectors return to 0 V differential.
4. Power down, connect one two-valve stack, then repower at 3.3 V. Repeat
   with both stacks. Compare the loaded waveform with the unloaded result
   and check that the stacked valves darken and clear together.
