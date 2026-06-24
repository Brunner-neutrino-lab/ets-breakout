#!/usr/bin/env python
"""Emit a PCBWay-style BOM CSV for a board, grouped by part.

  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/make_bom.py <board.kicad_pcb> <out.csv>
"""
import sys
import csv
import collections
import pcbnew

# footprint lib name -> (description, manufacturer, MPN, Digi-Key)
PARTS = {
    "SAMTEC_QSE-040-01-X-D-A":
        ("QSE-040 board-to-board socket (mates detector QTE-040)", "Samtec", "QSE-040-01-L-D-A", ""),
    "Samtec_MCX-J-P-X-ST-SM1":
        ("MCX jack, straight (vertical) surface-mount, 50 ohm", "Samtec", "MCX-J-P-H-ST-SM1", ""),
    "SMA_Amphenol_901-143_Horizontal":
        ("SMA jack, right-angle through-hole, 50 ohm", "Amphenol RF", "901-143-6RFX", "ARFX1232-ND"),
    "U.FL_Hirose_U.FL-R-SMT-1_Vertical":
        ("U.FL jack, SMT  [<=60 V working voltage - low-bias use only]", "Hirose", "U.FL-R-SMT-1(10)", ""),
    "SMP_Amphenol_SMP-MSSB-PCS_Vertical":
        ("SMP male jack, vertical SMT smooth-bore, 50 ohm  [centre via-in-pad - plug/cap or hand-solder]", "Amphenol RF", "SMP-MSSB-PCS", ""),
    "MountingHole_3.2mm_M3":
        ("M3 mounting hole, non-plated", "", "", ""),
}


def main():
    board = pcbnew.LoadBoard(sys.argv[1])
    groups = collections.defaultdict(list)
    for fp in board.GetFootprints():
        name = str(fp.GetFPID().GetLibItemName())
        groups[name].append(str(fp.GetReference()))
    rows = []
    for name, refs in groups.items():
        desc, mfr, mpn, dk = PARTS.get(name, (name, "", "", ""))
        refs = sorted(refs)
        rows.append([", ".join(refs), len(refs), desc, mfr, mpn, dk, name])
    rows.sort(key=lambda r: -r[1])
    with open(sys.argv[2], "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designators", "Qty", "Description", "Manufacturer",
                    "MPN", "Digi-Key", "KiCad Footprint"])
        w.writerows(rows)
    print(f"wrote {sys.argv[2]}: {sum(r[1] for r in rows)} parts in {len(rows)} lines")


if __name__ == "__main__":
    main()
