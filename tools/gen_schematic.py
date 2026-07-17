#!/usr/bin/env python
"""Generate the human-review schematic from pinout.py (the single source of truth).

The boards are generated directly from pinout.py (no netlist-driven flow); this schematic
is a REFERENCE artifact for human review of the J5 fanout. It is built from the very same
pinout.py the board generator uses, so it cannot drift from the boards. Do not hand-edit
the output — rerun this script.

  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/gen_schematic.py
  -> docs/schematic/ets-breakout.kicad_sch

Validate / export:
  kicad-cli sch erc docs/schematic/ets-breakout.kicad_sch
  kicad-cli sch export pdf docs/schematic/ets-breakout.kicad_sch -o docs/schematic/ets-breakout.pdf

Layout: J5 (QSE-040) on the left with pin NAMES = net names straight from J5_PINOUT;
25 coax jacks (refs = board refs K0..K23 + IV) in a grid on the right; connectivity by
net labels; THERM4/THERM5 no-connected (excluded per spec). A KiCad netlist export of
this sheet reproduces the pinout.py map (checked in-session 2026-07-11).
"""
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from pinout import J5_PINOUT, BREAKOUT_SIGNALS, EXCLUDED_SIGNALS, GROUND_NET

OUT = os.path.join(os.path.dirname(HERE), "docs", "schematic", "ets-breakout.kicad_sch")
NS = uuid.UUID("c7e5a9d1-0000-4000-8000-00000000e75b")  # ets-breakout schematic namespace
VERSION = "20260306"
JACK_VALUE = "MCX-J-P-H-ST-TH1"          # Board A (final variant, through-hole); B/C/D differ only in jack part
JACK_FP = "Samtec_MCX-J-P-H-ST-TH1"
J5_FP = "SAMTEC_QSE-040-01-X-D-A"


def uid(*parts):
    return str(uuid.uuid5(NS, ":".join(str(p) for p in parts)))


# ---------- ordered pin lists (odd + G1..G4 left, even + G5..G8 right) ----------------
LEFT_PINS = [p for p in range(1, 81, 2)] + ["G1", "G2", "G3", "G4"]
RIGHT_PINS = [p for p in range(2, 81, 2)] + ["G5", "G6", "G7", "G8"]
NPS = len(LEFT_PINS)                      # 44 pins per side
PITCH = 2.54
HALF = (NPS - 1) * PITCH / 2              # 54.61 -> pins at +-HALF in symbol coords (Y-up)

# ---------- lib_symbols ----------------------------------------------------------------


def _pin(ptype, x, y, ang, length, name, number):
    return ('\t\t\t(pin %s line\n\t\t\t\t(at %s %s %d)\n\t\t\t\t(length %s)\n'
            '\t\t\t\t(name "%s" (effects (font (size 1.27 1.27))))\n'
            '\t\t\t\t(number "%s" (effects (font (size 1.27 1.27))))\n\t\t\t)'
            % (ptype, x, y, ang, length, name, number))


def qse_symbol():
    pins = []
    for i, p in enumerate(LEFT_PINS):
        pins.append(_pin("passive", -20.32, HALF - i * PITCH, 0, 5.08, J5_PINOUT[p], p))
    for i, p in enumerate(RIGHT_PINS):
        pins.append(_pin("passive", 20.32, HALF - i * PITCH, 180, 5.08, J5_PINOUT[p], p))
    body = ('\t\t(symbol "QSE-040-01-L-D-A_0_1"\n'
            '\t\t\t(rectangle (start -15.24 %s) (end 15.24 -%s)\n'
            '\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background))\n\t\t\t)\n\t\t)'
            % (HALF + 2.54, HALF + 2.54))
    return ('\t(symbol "ets:QSE-040-01-L-D-A"\n'
            '\t\t(pin_names (offset 1.016))\n'
            '\t\t(exclude_from_sim no) (in_bom yes) (on_board yes)\n'
            '\t\t(property "Reference" "J" (at 0 %s 0) (effects (font (size 1.27 1.27))))\n'
            '\t\t(property "Value" "QSE-040-01-L-D-A" (at 0 -%s 0) (effects (font (size 1.27 1.27))))\n'
            '\t\t(property "Footprint" "%s" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
            '\t\t(property "Datasheet" "Samtec_QSE.pdf" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
            '%s\n\t\t(symbol "QSE-040-01-L-D-A_1_1"\n%s\n\t\t)\n\t)'
            % (HALF + 5.08, HALF + 5.08, J5_FP, body, "\n".join(pins)))


def jack_symbol():
    pins = _pin("passive", -8.89, 1.27, 0, 5.08, "SIG", "1") + "\n" + \
           _pin("passive", -8.89, -1.27, 0, 5.08, "SHLD", "2")
    gfx = ('\t\t(symbol "COAX_JACK_0_1"\n'
           '\t\t\t(circle (center 0 1.27) (radius 2.2) (stroke (width 0.254) (type default)) (fill (type none)))\n'
           '\t\t\t(circle (center 0 1.27) (radius 0.4) (stroke (width 0.254) (type default)) (fill (type outline)))\n'
           '\t\t\t(polyline (pts (xy -3.81 -1.27) (xy -1.55 -1.27) (xy -1.55 -0.28))\n'
           '\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none))\n\t\t\t)\n\t\t)')
    return ('\t(symbol "ets:COAX_JACK"\n'
            '\t\t(pin_names (offset 1.016) (hide yes))\n'
            '\t\t(exclude_from_sim no) (in_bom yes) (on_board yes)\n'
            '\t\t(property "Reference" "K" (at 0 6.35 0) (effects (font (size 1.27 1.27))))\n'
            '\t\t(property "Value" "%s" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))\n'
            '\t\t(property "Footprint" "%s" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
            '\t\t(property "Datasheet" "mcx-j-p-x-st-th1-mkt.pdf" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))\n'
            '%s\n\t\t(symbol "COAX_JACK_1_1"\n%s\n\t\t)\n\t)' % (JACK_VALUE, JACK_FP, gfx, pins))


# ---------- sheet-level emitters --------------------------------------------------------

def wire(x1, y1, x2, y2):
    return ('\t(wire\n\t\t(pts (xy %s %s) (xy %s %s))\n'
            '\t\t(stroke (width 0) (type default))\n\t\t(uuid "%s")\n\t)'
            % (x1, y1, x2, y2, uid("wire", x1, y1, x2, y2)))


def label(net, x, y, justify):
    return ('\t(label "%s"\n\t\t(at %s %s 0)\n'
            '\t\t(effects (font (size 1.27 1.27)) (justify %s))\n\t\t(uuid "%s")\n\t)'
            % (net, x, y, justify, uid("label", net, x, y)))


def no_connect(x, y):
    return '\t(no_connect\n\t\t(at %s %s)\n\t\t(uuid "%s")\n\t)' % (x, y, uid("nc", x, y))


def sym_instance(lib_id, ref, value, x, y, iu):
    return ('\t(symbol\n\t\t(lib_id "%s")\n\t\t(at %s %s 0)\n\t\t(unit 1)\n\t\t(body_style 1)\n'
            '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n'
            '\t\t(dnp no)\n\t\t(uuid "%s")\n'
            '\t\t(property "Reference" "%s" (at %s %s 0) (effects (font (size 1.27 1.27))))\n'
            '\t\t(property "Value" "%s" (at %s %s 0) (effects (font (size 1.0 1.0))))\n'
            '\t\t(instances\n\t\t\t(project "ets-breakout"\n\t\t\t\t(path "/%s" (reference "%s") (unit 1))\n\t\t\t)\n\t\t)\n\t)'
            % (lib_id, x, y, iu, ref,
               x, y - (HALF + 7.62) if lib_id == "ets:QSE-040-01-L-D-A" else y - 6.35,
               value, x, y + (HALF + 7.62) if lib_id == "ets:QSE-040-01-L-D-A" else y + 6.35,
               ROOT, ref))


def text(s, x, y, size=2.0):
    return ('\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at %s %s 0)\n'
            '\t\t(effects (font (size %s %s)) (justify left bottom))\n\t\t(uuid "%s")\n\t)'
            % (s, x, y, size, size, uid("text", s)))


ROOT = uid("root")


def main():
    nodes = []

    # ---- J5 ----
    j5x, j5y = 63.5, 148.59
    nodes.append(sym_instance("ets:QSE-040-01-L-D-A", "J5", "QSE-040-01-L-D-A", j5x, j5y, uid("J5")))
    # a KiCad pin's (at ...) IS the connection point; length extends toward the body
    for side, pins, xoff, xstub, just in (
            ("L", LEFT_PINS, -20.32, -3.81, "right bottom"),
            ("R", RIGHT_PINS, 20.32, 3.81, "left bottom")):
        for i, p in enumerate(pins):
            net = J5_PINOUT[p]
            px = round(j5x + xoff, 2)
            py = round(j5y - (HALF - i * PITCH), 2)          # schematic Y-down
            if net in EXCLUDED_SIGNALS:
                nodes.append(no_connect(px, py))
                continue
            ex = round(px + xstub, 2)
            nodes.append(wire(px, py, ex, py))
            nodes.append(label(net, ex, py, just))

    # ---- jacks: refs match the board (J6..J30; channel identity is the net label) ----
    jacks = [("J%d" % (6 + i), "SIPM_K%d" % i) for i in range(24)] + [("J30", "IV")]
    cols, dx, dy, x0, y0 = 5, 45.72, 45.72, 190.5, 50.8
    for n, (ref, net) in enumerate(jacks):
        jx = round(x0 + (n % cols) * dx, 2)
        jy = round(y0 + (n // cols) * dy, 2)
        nodes.append(sym_instance("ets:COAX_JACK", ref, JACK_VALUE, jx, jy, uid("jack", ref)))
        for pin_dy, pnet in ((-1.27, net), (1.27, GROUND_NET)):   # SIG at -1.27 (Y-down), SHLD below
            px = round(jx - 8.89, 2)
            py = round(jy + pin_dy, 2)
            ex = round(px - 3.81, 2)
            nodes.append(wire(px, py, ex, py))
            nodes.append(label(pnet, ex, py, "right bottom"))

    # ---- notes ----
    nodes.append(text("GENERATED from pinout.py by tools/gen_schematic.py - do not hand-edit.", 190.5, 271.78))
    nodes.append(text("Reference schematic for human review; boards are generated directly from pinout.py.", 190.5, 276.86))
    nodes.append(text("IV spans J5 pins 40 + 42 (both labeled). THERM4/THERM5 not broken out (per spec).", 190.5, 281.94))
    nodes.append(text("Jack part per variant: A=MCX-J-P-H-ST-TH1  B=901-143-6RFX  C=U.FL-R-SMT-1(10)  D=SMP-MSLD-PCS-20", 190.5, 287.02))

    tb = ('\t(title_block\n\t\t(title "ETS per-channel SiPM breakout - J5 fanout (25 coax jacks)")\n'
          '\t\t(date "2026-07-11")\n\t\t(company "Brunner lab")\n'
          '\t\t(comment 1 "GENERATED from pinout.py - regenerate with tools/gen_schematic.py")\n\t)')

    out = ('(kicad_sch\n\t(version %s)\n\t(generator "gen_schematic.py")\n\t(generator_version "10.0")\n'
           '\t(uuid "%s")\n\t(paper "A3")\n%s\n\t(lib_symbols\n%s\n%s\n\t)\n%s\n'
           '\t(sheet_instances\n\t\t(path "/" (page "1"))\n\t)\n)\n'
           % (VERSION, ROOT, tb, qse_symbol(), jack_symbol(), "\n".join(nodes)))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote %s: J5 (88 pins) + %d jacks, %d nodes" % (OUT, len(jacks), len(nodes)))


if __name__ == "__main__":
    main()
