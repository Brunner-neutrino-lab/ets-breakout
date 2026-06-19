"""Single source of truth for the ETS per-channel SiPM breakout boards.

The breakout boards replace the (broken) ``iv-pulse-mux`` board in the Brunner-lab
ETS-96-channel-IV-pulse-mux system. Each board mates the detector-side connector
**J5 = QSE-040-01-L-D-A** and fans each individual SiPM channel + the IV line out to
its own coaxial jack (MCX on Board A, SMA on Board B).

The pin->net map below is the AUTHORITATIVE QSE-040 (J5) pinout, derived from the
upstream schematic netlist:

    kicad-cli sch export netlist --format kicadsexpr iv-pulse-mux.kicad_sch
    -> net blocks, connector ref "J5" (Channels.kicad_sch)

verified 2026-06-16. Do NOT hand-edit individual pin numbers to "fix" a layout —
if the upstream board changes, re-export the netlist and regenerate this map so it
stays a single source of truth.

Integer keys 1..80 are the signal contacts; "G1".."G8" are the connector's
ground/shield pads. Every signal contact is flanked by GNDA (ground-signal-ground),
which is what makes a clean coax fan-out possible.
"""

GROUND_NET = "GNDA"

# QSE-040-01-L-D-A (J5) : pin -> net  (authoritative; from netlist export)
J5_PINOUT = {
    1: "GNDA",     2: "SIPM_K7",  3: "GNDA",     4: "GNDA",
    5: "GNDA",     6: "SIPM_K6",  7: "GNDA",     8: "GNDA",
    9: "GNDA",    10: "SIPM_K5", 11: "GNDA",    12: "GNDA",
    13: "GNDA",   14: "SIPM_K4", 15: "GNDA",    16: "GNDA",
    17: "GNDA",   18: "SIPM_K3", 19: "GNDA",    20: "GNDA",
    21: "GNDA",   22: "SIPM_K2", 23: "GNDA",    24: "GNDA",
    25: "GNDA",   26: "SIPM_K1", 27: "SIPM_K8", 28: "GNDA",
    29: "GNDA",   30: "SIPM_K0", 31: "SIPM_K9", 32: "GNDA",
    33: "GNDA",   34: "GNDA",    35: "SIPM_K10",36: "GNDA",
    37: "GNDA",   38: "GNDA",    39: "SIPM_K11",40: "IV",
    41: "SIPM_K12",42: "IV",     43: "GNDA",    44: "GNDA",
    45: "SIPM_K13",46: "GNDA",   47: "GNDA",    48: "GNDA",
    49: "SIPM_K14",50: "GNDA",   51: "GNDA",    52: "SIPM_K23",
    53: "SIPM_K15",54: "GNDA",   55: "GNDA",    56: "SIPM_K22",
    57: "GNDA",   58: "GNDA",    59: "GNDA",    60: "SIPM_K21",
    61: "GNDA",   62: "GNDA",    63: "GNDA",    64: "SIPM_K20",
    65: "GNDA",   66: "GNDA",    67: "GNDA",    68: "SIPM_K19",
    69: "GNDA",   70: "GNDA",    71: "GNDA",    72: "SIPM_K18",
    73: "GNDA",   74: "GNDA",    75: "GNDA",    76: "SIPM_K17",
    77: "THERM4", 78: "GNDA",    79: "THERM5",  80: "SIPM_K16",
    "G1": "GNDA", "G2": "GNDA",  "G3": "GNDA",  "G4": "GNDA",
    "G5": "GNDA", "G6": "GNDA",  "G7": "GNDA",  "G8": "GNDA",
}

# Signals that get broken out to their own coax jack, in jack order.
# 24 SiPM channels + IV = 25 jacks per board.
BREAKOUT_SIGNALS = [f"SIPM_K{i}" for i in range(24)] + ["IV"]

# Present on the connector but intentionally NOT broken out (per spec).
EXCLUDED_SIGNALS = ("THERM4", "THERM5")


def net_to_pins(net):
    """Return the sorted list of J5 pins carrying ``net`` (ints before G-pads)."""
    pins = [p for p, n in J5_PINOUT.items() if n == net]
    return sorted(pins, key=lambda p: (isinstance(p, str), p))


def breakout_map():
    """signal -> [QSE-040 pin(s)] for every broken-out jack (IV spans pins 40 & 42)."""
    return {sig: net_to_pins(sig) for sig in BREAKOUT_SIGNALS}


if __name__ == "__main__":
    for sig, pins in breakout_map().items():
        print(f"{sig:<10} -> J5 pin(s) {', '.join(map(str, pins))}")
    gnd = net_to_pins(GROUND_NET)
    print(f"\n{len(BREAKOUT_SIGNALS)} jacks; {len(gnd)} GNDA contacts "
          f"({sum(isinstance(p, int) for p in gnd)} signal-row + "
          f"{sum(isinstance(p, str) for p in gnd)} G-pads)")
