#!/usr/bin/env python
"""Import a FreeRouting Specctra session (.ses) back onto a board (routed tracks + vias).

  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/import_ses.py <board.kicad_pcb> [file.ses]
  default ses = <board>.ses ; writes the routed tracks back over the .kicad_pcb in place.

The .ses carries only routing (wires/vias keyed by the same net/component names), so the
placement, outline and zones are preserved and only copper is added. Method ported from the
multi-channel-cremat-amplifier repo (hardware/import_ses.py).
"""
import os
import sys
import pcbnew

pcb = sys.argv[1]
ses = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(pcb)[0] + ".ses"
b = pcbnew.LoadBoard(pcb)
try:
    ok = pcbnew.ImportSpecctraSES(b, ses)
except TypeError:
    ok = pcbnew.ImportSpecctraSES(ses)
pcbnew.SaveBoard(pcb, b)
print("SES import %s from %s ; saved routed board" % ("OK" if ok else "FAILED", ses))
sys.exit(0 if ok else 1)
