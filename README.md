# Strobe Glasses

Have you been seeing too much? Disappointed by the lack of stuttering in your reality? Introducing Strobe Glasses.

Open-source strobe glasses for experimenting with visual reaction-time training.

![Angled KiCad renders of the MK1 PCB](assets/pcb-front-back.png)

Two stacked LCD light valves per eye switch between light and dark at an adjustable
rate, periodically interrupting vision. The goal is a small, USB-C rechargeable
control board that fits into a 3D-printed glasses frame.

The MK1 PCB uses an ATtiny402, with USB-C charging and an output for each eye.

[KiCad project](strobeGlassesMK1/) · [Parts and assembly](hardware-library/BOM.md) · [Firmware](firmware/strobe_glasses/)

![Voltage decay across one LCD valve after disabling the 5 V PSU output](assets/lcd-5v-psu-off.png)

Electrical decay after disabling the 5 V PSU output (90–10%: 477 ms).
Shorting the valve leads clears it much faster.
