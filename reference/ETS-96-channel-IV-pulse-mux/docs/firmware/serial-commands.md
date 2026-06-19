# Serial Command Reference

## Connection Parameters

| Parameter | Value |
|---|---|
| Baud rate | 9600 bps |
| Data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Flow control | None |
| Line ending | `\n` or `\r` (either accepted) |

**Interface:** Arduino Nano Every USB-to-UART (appears as a virtual COM port).

Connect with any serial terminal program (e.g., Arduino Serial Monitor, PuTTY, minicom, screen). Send a blank line (press Enter on an empty input) to print the help text.

---

## Command Summary

| Command | Syntax | Description |
|---|---|---|
| `a` | `a <channel>` | Activate single channel (bias + sense) |
| `b` | `b <channel> <state>` | Set bias relay state |
| `s` | `s <channel> <state>` | Set sense relay state |
| `w` | `w` | Write current state to relays |
| `z` | `z` | Zero all states and write |
| `d` | `d` | Dump current state (hex) |
| `t` | `t` | Read die temperature (Kelvin) |
| `Y` | `Y` | Activate bypass line |
| `y` | `y` | Deactivate bypass line |
| *(empty)* | *(blank line)* | Print help text |

> **Case sensitivity:** Most commands are case-insensitive (processed with `strcasecmp`). The exceptions are `y`/`Y` (bypass control), which are strictly case-sensitive.

---

## Command Descriptions

---

### `a` — Activate Channel

**Syntax:** `a <channel>`

**Arguments:**
- `<channel>` — integer, 1 to 96.

**Behavior:**
1. Zeros all relay states (equivalent to `z`).
2. Enables the bias relay for `<channel>`.
3. Enables the sense relay for the board containing `<channel>`.
4. Writes the new state to the shift registers.

**Use case:** The standard command for I-V curve acquisition. Activates exactly one channel and deactivates all others.

**Example:**
```
a 42
```
Activates channel 42 (Board 1, channel 18 on that board), deactivating all other channels.

**Response:**
```
Command: <a 42>
Activating
Command complete
```

---

### `b` — Set Bias Relay

**Syntax:** `b <channel> <state>`

**Arguments:**
- `<channel>` — integer, 1 to 96.
- `<state>` — integer, 1 (activate) or 0 (deactivate).

**Behavior:**
- Sets or clears the bias relay bit for `<channel>` in `outState[]`.
- Immediately calls `writeState()` to apply the change to hardware.
- Does **not** affect the sense relay or any other channel.

**Use case:** Fine-grained bias relay control for calibration, testing, or multi-channel bias scenarios.

**Example:**
```
b 5 1
```
Energizes the bias relay for channel 5.

```
b 5 0
```
De-energizes the bias relay for channel 5.

---

### `s` — Set Sense Relay

**Syntax:** `s <channel> <state>`

**Arguments:**
- `<channel>` — integer, 1 to 96.
- `<state>` — integer, 1 (activate) or 0 (deactivate).

**Behavior:**
- In IV-Pulse Mux mode: drives `iv_on_pins[board]` HIGH (1) or LOW (0) for the board containing `<channel>`. **Does not call `writeState()`.**
- In legacy IV Mux mode: sets/clears bit 15 in `outState[board]`, then calls `writeState()`.

> **Important:** After calling `s`, you must follow with a `w` command to apply any pending shift register state changes (bias relay state is not affected by `s` alone in IV-Pulse Mux mode, since the sense relay is a direct GPIO, not a shift register bit).

**Use case:** Enable or disable the sense path independently from the bias path (e.g., to verify relay isolation).

**Example:**
```
s 10 1
```
Enables the sense relay for the board containing channel 10 (Board 0).

---

### `w` — Write State

**Syntax:** `w`

**Behavior:**
- Serializes the current `outState[]` array to the MIC5891 shift registers.
- Pulses RCLK to latch the output register (activating relay coils).
- Does not change `outState[]`.

**Use case:** Apply a previously configured relay state after using `b` and/or `s` commands without automatic write, or after manual `outState[]` manipulation (if extended in firmware).

---

### `z` — Zero State

**Syntax:** `z`

**Behavior:**
1. Sets all elements of `outState[]` to 0.
2. Drives all `iv_on_pins[]` LOW (deactivates all sense relays).
3. Calls `writeState()` to immediately de-energize all relay coils.

**Use case:** Safe reset to ensure all channels are disconnected before switching to a new configuration.

---

### `d` — Dump State

**Syntax:** `d`

**Behavior:**
- Prints the current value of `outState[0]` through `outState[3]` as hexadecimal 32-bit words, one per line.
- Does not affect hardware state.

**Output format:**
```
1
0
400000
0
```
(Example: Board 0 has bit 0 set = channel 1 bias relay active; Board 2 has bit 22 set = channel 23 on Board 2 bias relay active.)

**Use case:** Verify the expected relay state before or after a sequence of commands.

---

### `t` — Temperature Read

**Syntax:** `t`

**Behavior:**
- Enters a loop, reading the ATmega4809 internal temperature sensor once per second.
- Prints the die temperature in **Kelvin** on each iteration.
- Loop continues until any character is received on the serial port.

**Output format:**
```
298.7
298.8
299.0
...
```

**Use case:** Monitor MCU temperature inside a vacuum enclosure, primarily for environmental awareness rather than precision measurement.

---

### `Y` / `y` — Bypass Control

**Syntax:** `Y` (activate) or `y` (deactivate)

> These commands are **case-sensitive**.

**Behavior:**
- `Y` (uppercase): drives Arduino pin 12 (`BYPASS`) HIGH.
- `y` (lowercase): drives Arduino pin 12 (`BYPASS`) LOW.

**Use case:** Enable or disable the bypass signal line, which routes around the relay matrix for calibration.

> **Note:** Pin 12 is a temporary assignment (noted in firmware comments). This should be corrected in a future hardware revision.

---

### *(empty)* — Help

**Syntax:** *(blank line — press Enter with no input)*

**Behavior:**
- Prints the on-device command help text.

**Example output (IV-Pulse Mux mode):**
```
a <channel>           : activate <channel>, clearing everything else and setting bias and sense
s <channel> <state>   : set sense relay of <channel> to <state>
t                     : print temperature (Kelvin) once per second until another character is received
b <channel> <state>   : set bias relay of <channel> to <state>
d                     : dump state
w                     : write state to relays
y                     : activate BYPASS if uppercase, deactivate if lowercase
z                     : zero state (and write to relays)
```

---

## Channel Numbering

Channels are numbered **1 to 96**. The mapping to physical boards is:

| Global Channel | Board Index | Channel on Board |
|---|---|---|
| 1–24 | Board 0 | 1–24 |
| 25–48 | Board 1 | 1–24 |
| 49–72 | Board 2 | 1–24 |
| 73–96 | Board 3 | 1–24 |

Internally, the firmware computes:
```cpp
board       = (channel - 1) / channelsPerBoard;   // 0–3
chanOnBoard = (channel - 1) % channelsPerBoard;   // 0–23
```

---

## Error Handling

- If a command handler returns a non-zero status (error), the firmware prints `"Error in command"`.
- Known error conditions: channel out of range (< 1 or > 96).
- Unrecognized commands print the help text and set error status.
- **Ctrl+C** (`0x03`) aborts the sequence (`q`) loop in legacy IV-Mux mode.

---

## Example Session

```
(press Enter for help)

a <channel>           : activate <channel>, ...
...

a 1
Command: <a 1>
Activating
Command complete

d
Command: <d>
Dump
1
0
0
0
Command complete

z
Command: <z>
Zero
Command complete

t
Command: <t>
298.6
298.7
(press any key to stop)
Command complete
```
