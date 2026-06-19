# ETS 96-Channel IV-Pulse Multiplexer

**Organization:** McGill University Physics – Electronic Design Support Group  
**Designer:** Eamon Egan  
**Schematic Date:** 2019-11-12 (Rev 1.0)  
**Design Tool:** KiCad 9.0  

---

## Overview

This repository contains the complete design files for a **96-channel I-V curve pulse multiplexer** used in detector physics instrumentation. The system routes bias voltage and sense signals to one of 96 detector channels (e.g., SiPMs or similar devices) under Arduino microcontroller command, enabling automated current-voltage (I-V) characterization of large detector arrays.

The system is organized as:
- **Four 24-channel Mux boards** (`iv-pulse-mux`) — each handling 24 detector channels via reed relays and shift registers.
- **One Motherboard** (`iv-pulse-motherboard`) — orchestrating all four mux boards, distributing power, and providing the interface to the control system.
- **Arduino firmware** (`Arduino code/iv-mux/iv-mux.ino`) — running on an Arduino Nano Every (ATmega4809), accepting serial commands to switch channels, read temperature, and control auxiliary lines.

---

## Repository Layout

```
.
├── README.md                          ← This file
├── docs/                              ← Project documentation
│   ├── architecture.md                ← System-level design overview
│   ├── hardware/
│   │   ├── iv-pulse-mux-board.md      ← IV Pulse Mux PCB documentation
│   │   ├── motherboard.md             ← Motherboard documentation
│   │   ├── component-libraries.md     ← Custom schematic and footprint libraries
│   │   └── pcb-design-rules.md        ← Net classes and PCB design rules
│   ├── firmware/
│   │   ├── firmware-overview.md       ← Arduino firmware architecture
│   │   └── serial-commands.md         ← Serial command protocol reference
│   ├── fabrication/
│   │   └── fabrication-guide.md       ← Fabrication and assembly guide
│   └── operation/
│       └── user-guide.md              ← System operation and integration guide
│
├── Arduino code/iv-mux/iv-mux.ino    ← Microcontroller firmware
│
├── iv-pulse-mux.kicad_pro             ← KiCad project: IV Pulse Mux board
├── iv-pulse-mux.kicad_sch             ← Root schematic (IV Pulse Mux)
├── iv-pulse-mux.kicad_pcb             ← PCB layout (IV Pulse Mux)
│
├── iv-pulse-motherboard.kicad_pro     ← KiCad project: Motherboard
├── iv-pulse-motherboard.kicad_sch     ← Root schematic (Motherboard)
├── iv-pulse-motherboard.kicad_pcb     ← PCB layout (Motherboard)
│
├── Channels.kicad_sch                 ← Hierarchical sheet: 24 channel cells
├── sense-relay.kicad_sch              ← Hierarchical sheet: single sense relay cell
├── sense-relays.kicad_sch             ← Hierarchical sheet: sense relay group
├── bias-relay.kicad_sch               ← Hierarchical sheet: single bias relay cell
├── bias-relays-with-control.kicad_sch ← Hierarchical sheet: bias relay group
├── control.kicad_sch                  ← Hierarchical sheet: shift register control
├── muxboard-interface.kicad_sch       ← Hierarchical sheet: board connector interface
│
├── iv-mux.pretty/                     ← Custom PCB footprint library
├── samtec-footprints.pretty/          ← Samtec QSE connector footprints
├── passthrough.pretty/                ← Panel passthrough connector footprints
├── bias-switches-symlibs/             ← Custom schematic symbol library
│
├── fab-files.kicad_jobset             ← Automated fabrication output job set
├── fabrication-toolkit-options.json   ← Gerber export settings
├── fp-lib-table                       ← KiCad footprint library table
├── sym-lib-table                      ← KiCad symbol library table
└── mcgill-university-2.*              ← McGill University logo (SVG/DXF/PNG)
```

---

## Quick-Start

### Hardware

1. Order PCBs and assemble using the [Fabrication Guide](docs/fabrication/fabrication-guide.md).
2. Stack up to four Mux boards on the Motherboard via the Samtec QSE-040 connectors.
3. Connect detector channels to MCX connectors on the Mux boards.
4. Apply bias supply and sense lines via the Motherboard.

### Firmware

1. Open `Arduino code/iv-mux/iv-mux.ino` in the Arduino IDE.
2. Ensure `#define IVPULSEMUX` is present (enabled by default).
3. Select board: **Arduino Mega or Mega 2560** (required for ATmega4809 / Nano Every with Mega2560 profile).
4. Upload to the Arduino Nano Every.
5. Open a serial terminal at **9600 baud**.
6. Type a blank line to print the command help.

For a full command reference, see the [Serial Commands Reference](docs/firmware/serial-commands.md).

---

## Documentation Index

| Document | Description |
|---|---|
| [System Architecture](docs/architecture.md) | Top-level design intent, block diagram, and signal flow |
| [IV Pulse Mux Board](docs/hardware/iv-pulse-mux-board.md) | Schematic, PCB, and component details for the 24-channel mux board |
| [Motherboard](docs/hardware/motherboard.md) | Schematic and PCB details for the control motherboard |
| [Component Libraries](docs/hardware/component-libraries.md) | Custom schematic symbols and PCB footprints |
| [PCB Design Rules](docs/hardware/pcb-design-rules.md) | Net classes, clearances, and trace width rules |
| [Firmware Overview](docs/firmware/firmware-overview.md) | Arduino firmware architecture and state machine |
| [Serial Commands](docs/firmware/serial-commands.md) | Complete serial command protocol reference |
| [Fabrication Guide](docs/fabrication/fabrication-guide.md) | PCB fab, BOM, and assembly instructions |
| [User / Operation Guide](docs/operation/user-guide.md) | How to operate and integrate the system |

---

## Known Issues / Open Items (Rev 1.0)

- `BYPASS` signal is connected to Arduino pin 12 as a **temporary workaround**; the comment in firmware notes this should be corrected in a future revision.
- The `iv_on_pins[]` array uses analog pins `A0–A3` instead of the originally intended `THERM1–THERM4` thermistor pins — firmware comment notes this was an oversight.
- Low-power sleep mode (`LOWPOWER_SLEEP`) was prototyped but **is currently disabled**; register access issues on the ATmega4809 need to be resolved.
- The `q` (sequence) command is **only available in non-IV-pulse-mux mode** (i.e., the older 6×15 channel variant).
- Symbol library `iv-mux-rescue` references an absolute path on the designer's machine (`C:/Users/eamon/...`) and must be remapped when opening on a different workstation.

---

## Revision History

| Rev | Date | Description |
|---|---|---|
| 1.0 | 2019-11-12 | Initial release (schematic date) |

---

## License

Hardware design files are the property of McGill University Physics, Electronic Design Support Group. Contact the Brunner Neutrino Lab for use and distribution terms.
