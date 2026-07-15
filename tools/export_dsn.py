#!/usr/bin/env python
"""Export a placed board to a Specctra .dsn for autorouting with FreeRouting.

  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/export_dsn.py <board.kicad_pcb> [signal_layer]
  -> <board>.dsn  (next to the .kicad_pcb)

If signal_layer is given (e.g. B.Cu), every OTHER copper layer is marked (type power) in the
DSN so FreeRouting routes signals only on that one layer -> a single-layer planar fan with no
vias. The ets breakout mounts the QSE on B.Cu and the through-hole jacks reach every layer, so
routing on B.Cu alone gives the zero-via, zero-crossing result. Omit the arg to leave all
copper layers routable.

The board must be placement-clean (no overlapping copper) or ExportSpecctraDSN returns False.
The default net-class track width set by finalize_board.py setup rides into the DSN, so
FreeRouting routes at the 50 ohm width. Method ported from the multi-channel-cremat-amplifier
repo (hardware/export_dsn.py) + the single-signal-layer restriction.
"""
import os
import re
import sys
import pcbnew

pcb = sys.argv[1]
signal_layer = sys.argv[2] if len(sys.argv) > 2 else None
dsn = os.path.splitext(pcb)[0] + ".dsn"
b = pcbnew.LoadBoard(pcb)
try:
    ok = pcbnew.ExportSpecctraDSN(b, dsn)
except TypeError:
    ok = pcbnew.ExportSpecctraDSN(dsn)
if not ok:
    print("DSN export FAILED -> %s" % dsn)
    sys.exit(1)

if signal_layer:
    # mark every copper layer except signal_layer as (type power) so FreeRouting treats it as
    # a plane and routes signals only on signal_layer (single-layer planar, no vias).
    txt = open(dsn, encoding="utf-8").read()

    def retype(m):
        name = m.group(1)
        typ = "signal" if name == signal_layer else "power"
        return "(layer %s\n      (type %s)" % (name, typ)

    txt, n = re.subn(r"\(layer (\S+)\s*\n\s*\(type signal\)", retype, txt)
    open(dsn, "w", encoding="utf-8").write(txt)
    print("DSN export OK -> %s (routing layer = %s; %d layers retyped)" % (dsn, signal_layer, n))
else:
    print("DSN export OK -> %s" % dsn)
sys.exit(0)
