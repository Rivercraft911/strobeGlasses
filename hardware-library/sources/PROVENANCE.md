# Library sources

Base package footprints, symbols and models come from the KiCad 10 libraries, adapted into the project-local `StrobeGlasses` library. The [KiCad library license](KiCad_Libraries_LICENSE.md) and [package-model license](KiCad_packages3D_LICENSE.md) apply to those assets.

The selected standard packages are SOIC-8, SOT-23-5, 0603 passives/LED, KEMET A-case tantalum, JST-SH SM02B-SRSS-TB, Omron B3U-3000P and GCT USB4125. Footprints retain the package geometry, with project procurement fields and board-level functional silkscreen. Package STEP files retain their source headers.

- [Microchip ATtiny202/402 family](https://ww1.microchip.com/downloads/aemDocuments/documents/MCU08/ProductDocuments/DataSheets/ATtiny202-204-402-404-406-DataSheet-DS40002318A.pdf)
- [Microchip MCP73831/2](https://ww1.microchip.com/downloads/en/DeviceDoc/MCP73831-Family-Data-Sheet-DS20001984H.pdf)
- [GCT USB4125 drawing](https://gct.co/files/drawings/usb4125.pdf)
- [JST SH drawing](https://www.jst-mfg.com/product/pdf/eng/eSH.pdf)
- [Omron B3U drawing](https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3u.pdf)
- [Same Sky SLW-662712-15A-SMT-TR drawing](https://www.sameskydevices.com/product/resource/slw-662712-15a-smt-tr.pdf)

The slide-switch footprint follows Same Sky revision 1.0 page 2: signal lands 0.8 × 1.5 mm, mechanical centers 7.3 × 2.2 mm and Ø0.9 mm locating holes. Its STEP model is a project-generated nominal body/terminal/actuator envelope based on that drawing, reserving 1.4 mm above the PCB.

Resistor and ceramic-capacitor symbols follow the rectangular JLC-import style used in Pigeon Vision, rebuilt on a 2.54 mm grid with passive electrical pins. The MCU symbol groups the four LCD outputs, preset button and UPDI while retaining the manufacturer pinout.

Other part-specific datasheets and supplier links are in the [BOM](../BOM.md). Cached PDFs, preparation scripts, alternate packages and earlier experiments stay outside the published hardware set.
