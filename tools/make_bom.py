#!/usr/bin/env python
"""Emit a fab-house BOM CSV for a board, grouped by part.

  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/make_bom.py <board.kicad_pcb> <out.csv>
"""
import sys
import csv
import collections
import pcbnew

# footprint lib name -> (description, manufacturer, MPN, Digi-Key, LCSC)
# LCSC column enables an optional JLCPCB mixed SMT(QSE)+THT(MCX) assembled build: QSE plain -A
# = C3652741 (exact Samtec part), MCX = C5137197 (BAT Wireless BWMCX-KE, a generic 50 ohm THT
# MCX jack; alt C49118404). Both are JLC-library "Extended" parts and the MCX needs JLC's
# through-hole assembly add-on. GATE before an assembled order: confirm the BWMCX-KE land
# pattern matches our footprint (centre signal + 4 grounds on 5.08 mm, drills 1.10/1.40) --
# not dimensionally verified. Baseline stays fab-only + hand-solder from DigiKey. See docs/BOM.md.
PARTS = {
    "SAMTEC_QSE-040-01-X-D-A":
        ("QSE-040 board-to-board socket (mates detector QTE-040)", "Samtec", "QSE-040-01-L-D-A",
         "SAM8124-ND", "C3652741"),
    "Samtec_MCX-J-P-H-ST-TH1":
        ("MCX jack, straight (vertical) through-hole, 50 ohm", "Samtec", "MCX-J-P-H-ST-TH1",
         "SAM8944-ND", "C5137197 (BWMCX-KE equiv; confirm footprint)"),
    "SMA_Amphenol_901-143_Horizontal":
        ("SMA jack, right-angle through-hole, 50 ohm", "Amphenol RF", "901-143-6RFX", "ARFX1232-ND", ""),
    "U.FL_Hirose_U.FL-R-SMT-1_Vertical":
        ("U.FL jack, SMT  [<=60 V working voltage - low-bias use only]", "Hirose", "U.FL-R-SMT-1(10)", "", ""),
    "SMP_Amphenol_SMP-MSLD-PCS-20":
        ("SMP jack, vertical SMT, 50 ohm (4.08 mm max height)", "Amphenol RF", "SMP-MSLD-PCS-20", "", ""),
    "MountingHole_3.2mm_M3":
        ("M3 mounting hole, non-plated", "", "", "", ""),
}


def main():
    board = pcbnew.LoadBoard(sys.argv[1])
    groups = collections.defaultdict(list)
    for fp in board.GetFootprints():
        name = str(fp.GetFPID().GetLibItemName())
        groups[name].append(str(fp.GetReference()))
    rows = []
    for name, refs in groups.items():
        desc, mfr, mpn, dk, lcsc = PARTS.get(name, (name, "", "", "", ""))
        refs = sorted(refs)
        rows.append([", ".join(refs), len(refs), desc, mfr, mpn, dk, lcsc, name])
    rows.sort(key=lambda r: -r[1])
    with open(sys.argv[2], "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designators", "Qty", "Description", "Manufacturer",
                    "MPN", "Digi-Key", "LCSC", "KiCad Footprint"])
        w.writerows(rows)
    print(f"wrote {sys.argv[2]}: {sum(r[1] for r in rows)} parts in {len(rows)} lines")


if __name__ == "__main__":
    main()
