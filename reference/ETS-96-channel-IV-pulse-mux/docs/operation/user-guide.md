# User and Operation Guide

This guide describes how to set up, configure, and operate the ETS 96-Channel IV-Pulse Multiplexer system for I-V curve measurements.

---

## System Overview

The ETS 96-channel IV-Pulse Multiplexer connects a single bias voltage source and sense/measurement instrument to one of 96 detector channels under software command. The system is designed for:

- Sequential I-V curve characterization of detector arrays (SiPMs, photodiodes, etc.).
- Pulsed bias operation (one channel at a time, selected by the controller).
- Integration with automated measurement software via a serial command interface.

---

## Hardware Setup

### Required Equipment

| Item | Description |
|---|---|
| 1× Motherboard | Assembled and tested |
| 4× IV Pulse Mux boards | Assembled and tested |
| 1× Arduino Nano Every | Flashed with current firmware |
| 1× Computer | For serial control (USB) |
| 1× Bias power supply | Voltage source for detector bias |
| 1× SMU or electrometer | Source-measure unit for I-V curves |
| Coaxial cables (MCX) | For individual channel connections |
| *(Optional)* Sync source | Function generator or instrument trigger output |

---

### Physical Assembly

1. **Stack mux boards** on the motherboard by mating the QSH (header) connectors on the mux boards into the QSE (socket) connectors on the motherboard.
2. **Connect detectors** to the MCX connectors on the mux boards. Channel numbers are silk-screened on the PCB:
   - Board 0: Channels 1–24
   - Board 1: Channels 25–48
   - Board 2: Channels 49–72
   - Board 3: Channels 73–96
3. **Connect bias supply** to the bias input on the motherboard (BNC or terminal block, labeled `BIAS_IN`).
4. **Connect sense line** from the SMU or electrometer to the sense input on the motherboard.
5. **Connect Arduino** to the control PC via USB.
6. *(Optional)* Connect external trigger source to the SYNC input (MCX/BNC).

---

### Power-Up Sequence

1. Ensure all relay states are in a known off condition (firmware initializes to zero on power-up).
2. Power the Arduino via USB.
3. Apply the bias supply (start at 0 V and ramp to operating voltage gradually).
4. Verify through the serial interface that all states are zero (`d` command should return four lines of `0`).
5. Activate channels as required for measurements.

### Power-Down Sequence

1. Ramp bias supply to 0 V.
2. Send `z` command to zero all relay states.
3. Power off the bias supply.
4. Disconnect USB / power off Arduino.

---

## Serial Interface

Connect to the Arduino Nano Every using any serial terminal at **9600 baud, 8N1, no flow control**.

On most operating systems, the Arduino Nano Every appears as:
- **Windows:** `COMx` (check Device Manager)
- **Linux:** `/dev/ttyACM0` or `/dev/ttyUSB0`
- **macOS:** `/dev/cu.usbmodem...`

### Example: Linux / macOS (using `screen`)
```bash
screen /dev/ttyACM0 9600
```

### Example: Windows (using PuTTY)
Select "Serial", enter the COM port, set speed to 9600, click Open.

Press **Enter** on an empty line to display the command help.

---

## Basic Operation

### Activating a Single Channel

To connect channel N to the bias and sense lines:
```
a <N>
```

Example — activate channel 42:
```
a 42
```

This:
1. Disconnects all other channels (zeros state).
2. Closes the bias relay for channel 42.
3. Enables the sense relay for Board 1 (which contains channels 25–48).
4. Applies the change to hardware.

The detector on channel 42 is now connected to both the bias supply and the sense instrument. You can now trigger an I-V sweep from the measurement instrument.

### Deactivating All Channels

```
z
```

### Verifying State

```
d
```

Returns four hex numbers representing the 24-bit bias relay state of each board. A `1` in bit position 0 of the first word means channel 1 is active.

---

## Automated I-V Sweep (Software Integration)

For fully automated multi-channel I-V characterization, the serial interface can be driven from a host script (Python, LabVIEW, MATLAB, etc.).

### Example Python Snippet

```python
import serial
import time

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=2)
time.sleep(2)  # wait for Arduino to reset after serial connection

def activate_channel(ch):
    cmd = f'a {ch}\n'
    ser.write(cmd.encode())
    response = ser.read_until(b'Command complete\n')
    return response

def zero_all():
    ser.write(b'z\n')
    ser.read_until(b'Command complete\n')

# Example: sweep channels 1 to 96
for channel in range(1, 97):
    activate_channel(channel)
    # --- trigger your SMU I-V sweep here ---
    time.sleep(0.1)  # allow relays to settle (~10 ms typical)

zero_all()
ser.close()
```

### Relay Settling Time

Allow at least **10–20 ms** after activating a channel before triggering a measurement. Reed relays have a typical operate/release time of 0.5–5 ms; allow additional time for contact bounce to settle in precision measurements.

---

## Bypass Line

The bypass signal (Arduino pin 12) can route a signal around the relay matrix:

```
Y      ← activate bypass (uppercase Y)
y      ← deactivate bypass (lowercase y)
```

The purpose and external circuit for the bypass line should be documented in the motherboard schematic. Verify its connection before use.

---

## Temperature Monitoring

The `t` command reads the ATmega4809 internal die temperature:

```
t
```

Output (Kelvin, one reading per second):
```
298.4
298.5
...
```

Press any key to stop. This is useful for monitoring the thermal environment if the system is deployed in an enclosed or vacuum space.

> **Important:** The die temperature reflects MCU self-heating plus ambient. It is not a precision measurement and should not be used as a calibrated temperature reference.

---

## Multi-Board Architecture Notes

All four mux boards operate in parallel from the same SRCLK and RCLK lines. When `a <channel>` is called:
- Only the board containing the requested channel will have a non-zero shift register state.
- The sense relay (`IV_ON`) for that board's Arduino pin is driven HIGH.
- All other boards have all relays de-energized.

This ensures that at any given time, **at most one detector channel** is connected to the bias and sense lines, preventing cross-talk or simultaneous connections.

---

## Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| No serial response | Wrong COM port or baud rate | Verify port and use 9600 baud, 8N1 |
| `Error in command` | Channel out of range (< 1 or > 96) | Use valid channel numbers |
| Relay does not actuate | Shift register not initialized | Send `z` then `a <ch>` again |
| All channels on board N not working | IV_ON signal not working | Check Arduino pin A(N) and PhotoMOS relay on that board |
| Channel heard clicking but no current measured | Sense relay not closing | Verify `iv_on_pins[board]` wiring and PhotoMOS relay |
| State does not update after `s` command | `s` does not auto-write in IV-pulse-mux mode | Follow `s` with `w` |
| Temperature reads as 0 or garbage | VREF not set up correctly | This is a firmware-level issue; check ATmega4809 ADC configuration |
| Firmware upload fails | Wrong board selected | Select "Arduino Mega or Mega 2560" in Arduino IDE — the Nano Every (ATmega4809) requires this board profile in this project; see [Firmware Overview](../firmware/firmware-overview.md) |

---

## Safety Precautions

1. **High voltage:** The bias supply may operate at tens to hundreds of volts depending on the detector type. Follow standard HV safety practices. Ensure the bias supply is ramped down before connecting or disconnecting detector cables.
2. **ESD:** Reed relays and detectors (SiPMs especially) are ESD-sensitive. Handle all boards and connectors with appropriate ESD precautions (grounded wrist strap, anti-static mat).
3. **Vacuum operation:** If the system is operated in a vacuum enclosure, ensure components have been properly outgassed and that no volatile materials are present.
4. **No simultaneous bias on multiple channels:** The firmware enforces single-channel operation with the `a` command. However, the `b` command allows direct bias relay control without zeroing — take care not to inadvertently connect bias to multiple channels simultaneously if using `b` directly.
