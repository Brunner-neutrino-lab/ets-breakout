# System Architecture

## Purpose

The ETS 96-Channel IV-Pulse Multiplexer is a relay-switched signal routing system designed to sequentially (or selectively) connect a single bias source and sense measurement instrument to one of **96 detector channels**. The primary use case is automated I-V (current-voltage) curve characterization of large detector arrays, such as Silicon Photomultipliers (SiPMs) or similar solid-state photodetectors used in particle physics experiments.

---

## System Block Diagram

```
                         ┌───────────────────────────────────────────┐
                         │             Motherboard                   │
                         │                                           │
  Serial (9600 baud) ────┤  Arduino Nano Every (ATmega4809)          │
  (USB or TTL UART)      │  ┌──────────────────────────────────┐     │
                         │  │  Firmware (iv-mux.ino)           │     │
                         │  │  - Command parser                │     │
                         │  │  - Relay state machine           │     │
                         │  │  - Shift register driver         │     │
                         │  └────────┬─────────────────────────┘     │
                         │           │  SPI-like shift reg. bus       │
                         │           │  (SRCLK, RCLK, SER0–SER3)     │
                         └───────────┼───────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────────────────────┐
                    │                │  QSE-040 board-to-board connector│
                    │    ┌───────────▼──────────────────┐             │
                    │    │      IV Pulse Mux Board 1     │  Channels   │
                    │    │   24 channels (CH1–CH24)      │  1–24  ─────┼──► MCX connectors
                    │    │   MIC5891 shift register      │             │
                    │    │   Reed relays (bias + sense)  │             │
                    │    └──────────────────────────────┘             │
                    │    ┌──────────────────────────────┐             │
                    │    │      IV Pulse Mux Board 2     │  Channels   │
                    │    │   24 channels (CH25–CH48)     │  25–48 ─────┼──► MCX connectors
                    │    └──────────────────────────────┘             │
                    │    ┌──────────────────────────────┐             │
                    │    │      IV Pulse Mux Board 3     │  Channels   │
                    │    │   24 channels (CH49–CH72)     │  49–72 ─────┼──► MCX connectors
                    │    └──────────────────────────────┘             │
                    │    ┌──────────────────────────────┐             │
                    │    │      IV Pulse Mux Board 4     │  Channels   │
                    │    │   24 channels (CH73–CH96)     │  73–96 ─────┼──► MCX connectors
                    │    └──────────────────────────────┘             │
                    │                                                  │
                    │    Common bias supply ────────────────────────► │
                    │    Common sense line  ◄────────────────────────  │
                    │    (routed through selected relay on active board)│
                    └──────────────────────────────────────────────────┘
```

---

## Design Partitioning

### Why Split Into Two Board Types?

| Concern | Solution |
|---|---|
| 96 channels is too large for a single PCB at acceptable density | Split into four identical 24-channel mux boards |
| Centralized control logic and power distribution | Dedicated motherboard with Arduino and bus connections |
| Modularity and replaceability | Standardized QSE-040 connector allows any mux board to be swapped |

### Channel Numbering

Channels are numbered **1 to 96** in firmware. The mapping to boards is:

| Channel Range | Mux Board | Arduino SER Pin |
|---|---|---|
| 1 – 24 | Board 0 | Pin 2 |
| 25 – 48 | Board 1 | Pin 3 |
| 49 – 72 | Board 2 | Pin 4 |
| 73 – 96 | Board 3 | Pin 5 |

---

## Signal Paths

Each channel has two independent relay-switched paths:

### Bias Path (Reed Relay — "Bias Relay")
- Connects the shared **bias voltage rail** to the selected detector channel.
- Controlled by a bit in the MIC5891 shift register output (bits 0–23 per board).
- Relay coil is driven via shift register output pin.

### Sense Path (PhotoMOS Relay — "IV_ON")
- Connects the shared **sense/measurement line** to the selected detector channel's sense node.
- Controlled by `iv_on_pins[board]` (Arduino analog output pins A0–A3).
- One sense relay per board — only one channel per board can be sensed at a time (this is sufficient because only one channel per board is activated at a time).

### Bypass Line
- A separate signal path that can be enabled (pin `BYPASS`, Arduino pin 12) to route around the relay matrix for calibration or diagnostic purposes.
- Flagged as a temporary routing workaround in firmware Rev 1.0.

---

## Shift Register Architecture

Each mux board contains one **MIC5891** 8-bit latched serial-in, parallel-out power shift register. Multiple MIC5891 devices may be chained to achieve the 24-bit output width per board.

```
Arduino ──SRCLK──────────┬──────────────────────────────────────────►
         RCLK  ──────────┤──────────────────────────────────────────►
                         │
         SER0 ──────► [MIC5891 Board 0, 24 bits] ──► relay coils
         SER1 ──────► [MIC5891 Board 1, 24 bits] ──► relay coils
         SER2 ──────► [MIC5891 Board 2, 24 bits] ──► relay coils
         SER3 ──────► [MIC5891 Board 3, 24 bits] ──► relay coils
```

- All four boards share the same `SRCLK` and `RCLK` lines.
- Each board has a dedicated `SER` (serial data) line, enabling simultaneous parallel loading.
- Data is clocked MSB-first (bit 23 first).
- The output enable (`OE`) is held high during initialization, then driven low to enable relay outputs only after all registers have been initialized.

---

## Control Interface

The Arduino Nano Every provides a **9600-baud UART** interface. Commands are single-character mnemonics followed by numeric arguments, terminated by `\n` or `\r`.

Key operations:
- **Activate a channel** (`a <ch>`) — closes bias and sense relays for one channel, opens all others.
- **Independent relay control** (`b`, `s`) — set individual relay states for calibration or diagnostic use.
- **Bypass control** (`y`/`Y`) — activate/deactivate the bypass signal line.
- **Temperature monitoring** (`t`) — read ATmega4809 internal die temperature in Kelvin.
- **State dump** (`d`) — print current relay state as hex words.

See [Serial Commands Reference](../firmware/serial-commands.md) for the complete protocol.

---

## Synchronization

A dedicated **sync pulse input** is provided on Arduino pin 8 (`SYNC_PULSE`). This is used in the sequence (`q`) command (non-pulse-mux variant) to synchronize channel switching to an external trigger (e.g., a falling-edge voltage transition from a measurement instrument).

In the IV-pulse-mux variant, the `q` command is disabled; triggering is expected to be handled externally.

---

## Operating Modes

The firmware supports two hardware variants via a compile-time flag:

| Mode | `#define` | Boards | Channels/Board | Total |
|---|---|---|---|---|
| IV Mux (legacy) | *(undefined)* | 6 | 15 | 90 |
| IV Pulse Mux (current) | `IVPULSEMUX` | 4 | 24 | 96 |

The PCB described in this repository is the **IV Pulse Mux** variant. The IV Mux variant used a 74HC595 shift register and a different sense relay scheme; its support remains in the firmware for backward compatibility.

---

## Design Considerations for Future Revisions

1. **BYPASS pin assignment** should be moved from the temporary pin 12 to a dedicated pin.
2. **Thermistor inputs** (`THERM1–THERM4`) should be correctly wired if thermal monitoring is desired; `iv_on_pins[]` currently occupies `A0–A3`.
3. **Low-power sleep mode** should be revisited using ATmega4809-specific register definitions.
4. **Symbol library path** for `iv-mux-rescue` is currently an absolute Windows path; migrate to a relative project path.
5. **Sequence command** (`q`) support for the IV-pulse-mux variant should be evaluated for future addition.
