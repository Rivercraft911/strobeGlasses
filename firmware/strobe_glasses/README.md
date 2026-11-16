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
clock **5 MHz internal**, and **millis()/micros() Timer → Disabled**.

1. Turn SW1 off and unplug the glasses' charging cable. Set the UPDI Friend
   to 3.3 V, then connect **PWR → TP2**, **GND → TP3**, and **UPDI → TP1**.
2. Select the programmer's serial port and **SerialUPDI – SLOW: 57600 baud**.
3. On initial setup, select **BOD 2.6 V**, **Enabled/Enabled**, and
   **EEPROM retained**. Run **Burn Bootloader** to apply those fuses with the
   standard ATtiny402 board selection.
4. Use **Sketch → Upload Using Programmer**. Remove the programmer and
   switch on to try it.

[UPDI Friend guide](https://learn.adafruit.com/adafruit-updi-friend?view=all)

To compile from the repository root with megaTinyCore 2.6.11 installed:

```sh
arduino-cli compile --fqbn megaTinyCore:megaavr:atxy2:chip=402,clock=5internal,millis=disabled,bodvoltage=2v6,bodmode=enabled,eesave=enable --build-path firmware/strobe_glasses/build firmware/strobe_glasses
```
