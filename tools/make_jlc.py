#!/usr/bin/env python
"""Generate JLCPCB assembly files (BOM + CPL) from a KiCad placement CSV.

  python tools/make_jlc.py <board-...-pos.csv> <out_dir>
  -> <out_dir>/<board>-jlc-bom.csv   (Comment, Designator, Footprint, LCSC Part #)
  -> <out_dir>/<board>-jlc-cpl.csv   (Designator, Mid X, Mid Y, Layer, Rotation)

These are the two files JLCPCB's SMT/assembly step expects — distinct from the DigiKey
hand-solder BOM. The DigiKey BOM leads with DigiKey PNs, so JLC reads it as DigiKey sourcing;
this BOM's `LCSC Part #` column is what makes JLC source/place from LCSC. The CPL is KiCad's
placement re-headed to JLC's column names (KiCad already exports Y-up / gerber-aligned
coordinates, so values pass through verbatim — only the headers change, which is why KiCad's
raw pos.csv is rejected).

Runs under plain Python (reads the CSV; no pcbnew). Regenerate the pos.csv first with
`kicad-cli pcb export pos --format csv --units mm`.

ASSEMBLY GATE: the MCX LCSC part (C5137197, BAT Wireless BWMCX-KE) is a generic 50 ohm THT MCX
equivalent — confirm its land pattern matches this footprint (centre signal + 4 grounds on
5.08 mm, drills 1.10/1.40) and its pin-1 rotation before ordering assembly. See docs/BOM.md.
"""
import os
import re
import csv
import sys
import collections

# footprint lib name -> (BOM comment, LCSC part number) for JLC-assembled parts.
JLC = {
    "SAMTEC_QSE-040-01-X-D-A": ("QSE-040-01-L-D-A socket", "C3652741"),
    "Samtec_MCX-J-P-H-ST-TH1": ("MCX jack 50R THT (BWMCX-KE)", "C5137197"),
}


def natkey(ref):
    m = re.match(r"([A-Za-z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def main():
    pos_path, outdir = sys.argv[1], sys.argv[2]
    base = os.path.basename(pos_path).replace("-pos.csv", "")
    rows = list(csv.DictReader(open(pos_path, newline="", encoding="utf-8")))

    # CPL: re-head KiCad's pos columns to JLCPCB's (values pass through).
    cpl = os.path.join(outdir, base + "-jlc-cpl.csv")
    with open(cpl, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in rows:
            if r["Package"] not in JLC:
                continue
            w.writerow([r["Ref"], r["PosX"], r["PosY"], r["Side"].capitalize(), r["Rot"]])

    # BOM: one line per part, grouped by footprint, with the LCSC part number.
    groups = collections.defaultdict(list)
    for r in rows:
        if r["Package"] in JLC:
            groups[r["Package"]].append(r["Ref"])
    bom = os.path.join(outdir, base + "-jlc-bom.csv")
    with open(bom, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for fp, refs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            comment, lcsc = JLC[fp]
            w.writerow([comment, ",".join(sorted(refs, key=natkey)), fp, lcsc])

    print("wrote %s (%d parts) and %s (%d BOM lines)"
          % (os.path.basename(cpl), sum(len(v) for v in groups.values()),
             os.path.basename(bom), len(groups)))


if __name__ == "__main__":
    main()
