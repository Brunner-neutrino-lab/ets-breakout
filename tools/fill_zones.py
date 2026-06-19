#!/usr/bin/env python
"""Fill GND zones on a saved board (separate pass; in-memory Fill segfaults).

  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/fill_zones.py <board.kicad_pcb>
"""
import sys
import pcbnew

path = sys.argv[1]
board = pcbnew.LoadBoard(path)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(path)
print(f"filled {len(list(board.Zones()))} zones in {path}")
