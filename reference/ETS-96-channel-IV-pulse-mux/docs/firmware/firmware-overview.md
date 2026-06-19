# Firmware Overview

**File:** `Arduino code/iv-mux/iv-mux.ino`  
**Target Hardware:** Arduino Nano Every (ATmega4809)  
**Arduino Board Profile:** Mega 2560 (required for Nano Every in this configuration)  
**Baud Rate:** 9600 bps  

---

## Overview

The firmware provides a simple command-line interface over a serial UART connection to control the relay state of the ETS 96-Channel IV-Pulse Multiplexer. It:

- Accepts text commands over `Serial` (USB-to-UART on Arduino Nano Every).
- Maintains a software representation of the relay states in memory (`outState[]`).
- Serializes relay state to the MIC5891 shift registers via a bit-bang SPI-like protocol.
- Provides temperature readout via the ATmega4809 internal temperature sensor.
- Supports a bypass line control signal.

---

## Build Configuration

### Compile-Time Mode Selection

The firmware supports two hardware variants via a preprocessor flag:

```cpp
// When defined: IV-Pulse Mux (4 boards × 24 channels = 96 channels)
#define IVPULSEMUX

// When undefined: IV Mux (6 boards × 15 channels = 90 channels, legacy)
```

**The IV-Pulse Mux variant (`#define IVPULSEMUX`) is the current and intended build.**

The legacy IV Mux variant (undefined) uses 74HC595 shift registers and a different sense relay scheme. It is retained for backward compatibility but should not be used with the current PCB hardware.

### Key Constants (IV-Pulse Mux Mode)

```cpp
const int boardCount       = 4;    // four mux boards
const int channelsPerBoard = 24;   // 24 relay channels per board
const int maxChan          = 96;   // total channel count

int serPins[4]      = { 2, 3, 4, 5 };      // SER0–SER3 data lines
int iv_on_pins[4]   = { A0, A1, A2, A3 };  // sense relay enables

const int SRCLK    = 9;   // shift register serial clock
const int RCLK     = 10;  // shift register latch (output register strobe)
const int SRCLR    = 11;  // asynchronous clear (active low) [assigned to OE in IVPULSEMUX]
const int OE       = 11;  // output enable (active low) [IVPULSEMUX only]
const int BYPASS   = 12;  // bypass signal [temporary pin assignment]
const int SYNC_PULSE = 8; // external sync/trigger input
```

---

## Relay State Representation

The relay state is stored in a 32-bit word array:

```cpp
uint32_t outState[4];  // one word per mux board
```

Each word has **24 active bits** (bits 23–0), where each bit corresponds to a bias relay coil on that board:

- Bit 0 → Channel 1 on that board (e.g., global Channel 1 for Board 0)
- Bit 23 → Channel 24 on that board (e.g., global Channel 24 for Board 0)

The **sense relay** is not encoded in `outState`. Instead, it is controlled directly by driving `iv_on_pins[board]` HIGH or LOW.

---

## Shift Register Write Protocol

The `writeState()` function serializes `outState[]` to the MIC5891 shift registers using a bit-bang protocol:

```
For each of the 24 bits (MSB first, bit 23 down to bit 0):
    Set SER0–SER3 simultaneously (each board's bit for this position)
    Pulse SRCLK HIGH → LOW  (clock in the bit)

After all 24 bits:
    Pulse RCLK HIGH → LOW   (latch output registers → relay coils energized)
```

All four boards are loaded **simultaneously** in each SRCLK pulse, minimizing the time between the first board and last board activating their relays.

---

## Command Processing

The main loop polls for serial input one character at a time. When a newline (`\n` or `\r`) is received, the accumulated buffer is tokenized and dispatched to the appropriate command handler.

### State Machine

```
                  ┌─────────────────────────────────┐
                  │              loop()              │
                  │                                  │
  Serial input ──►│  Read char → append to inbuf    │
                  │                                  │
                  │  On '\n' or '\r':                │
                  │    tokenize(command, arg1, arg2) │
                  │    dispatch command              │
                  │    print status                  │
                  │    clear buffer                  │
                  └─────────────────────────────────┘
```

### Command Dispatch Table

| Command | Function Called | Side Effect |
|---|---|---|
| `a` | `channelActive(chan)` | Zeros state, sets bias+sense for one channel, writes to hardware |
| `b` | `setBiasRelayState(chan, state)` + `writeState()` | Updates bias relay bit and immediately writes |
| `s` | `setSenseRelayState(chan, state)` | Updates sense relay (IV_ON pin); does NOT auto-write in IV-pulse-mux mode |
| `w` | `writeState()` | Writes current `outState[]` to hardware |
| `z` | `zeroState()` + `writeState()` | Clears all relay states and writes |
| `d` | `dumpState()` | Prints `outState[]` as 4 hex words |
| `t` | `tempRead()` | Reads ATmega4809 internal ADC temp sensor, prints Kelvin until keypress |
| `Y` | `digitalWrite(BYPASS, HIGH)` | Activates bypass line |
| `y` | `digitalWrite(BYPASS, LOW)` | Deactivates bypass line |
| *(empty)* | `printHelp()` | Prints command summary |

---

## Initialization Sequence (`setup()`)

1. Start Serial at 9600 baud.
2. Configure GPIO pins (SER0–3, IV_ON0–3, SRCLK, RCLK, OE, BYPASS, SYNC_PULSE).
3. Set OE HIGH (disable outputs) while initializing.
4. Zero all relay states (`zeroState()`).
5. Write zero state to shift registers (`writeState()`).
6. Set OE LOW (enable outputs) — relays now active.

This sequence ensures no relay is accidentally energized during power-up.

---

## Temperature Sensor

The `tempRead()` function reads the **ATmega4809 internal temperature sensor** using the on-chip ADC:

- Uses the `TEMPSENSE` mux channel (`ADC0.MUXPOS = 0x1E`).
- Sets VREF to internal 1.1 V reference.
- Applies maximum initialization and sample delay for accuracy.
- Converts raw ADC value to Kelvin using calibration constants from the signature row:
  ```
  Temperature (K) = (ADC_result - SIGROW_TEMPSENSE1) × (SIGROW_TEMPSENSE0 / 256.0)
  ```
- Prints a reading every 1 second until any serial character is received.

> **Note:** The internal die temperature is useful for monitoring thermal environment inside a vacuum enclosure but will reflect self-heating from the MCU itself. It is not a substitute for a precision external temperature sensor.

---

## Synchronization Pulse (`SYNC_PULSE`, Pin 8)

The `SYNC_PULSE` input is provided for synchronizing channel switching to an external trigger signal (e.g., a falling-edge voltage pulse from a measurement instrument). This is used by the `sequence()` function in the non-IV-pulse-mux legacy mode:

- When `delay < 0` in the `q` command, the firmware waits for a negative-going pulse on pin 8 that is at least `MIN_PULSE = 500 µs` wide before advancing to the next channel.
- In IV-pulse-mux mode, this pin is reserved but the `q` command is not compiled in.

---

## Low-Power Sleep Mode (Disabled)

The firmware includes a dormant implementation of low-power sleep (`LOWPOWER_SLEEP 0`). The intent was to reduce heat dissipation when the system is deployed in a vacuum enclosure. The implementation was abandoned because:

- ATmega4809 sleep register access failed to compile under the Mega2560 profile used for Nano Every.
- The `SLEEP_MODE_IDLE` mode was targeted.

This should be revisited in a future firmware revision using ATmega4809-specific sleep APIs.

---

## Ctrl+C Abort

A `CTRL_C` (`0x03`) character received during a sequence operation aborts the active sequence loop. This is the only form of in-progress command abort available.

---

## Building and Uploading

1. Install the **Arduino IDE** (1.8.x or 2.x).
2. Open `Arduino code/iv-mux/iv-mux.ino`.
3. Under **Tools → Board**, select **Arduino Mega or Mega 2560**.
4. Confirm `#define IVPULSEMUX` is present.
5. Connect the Arduino Nano Every via USB.
6. Click **Upload**.
7. Open the **Serial Monitor** at 9600 baud, no line ending or newline, to test commands.
