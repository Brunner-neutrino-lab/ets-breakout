#!/usr/bin/env python
"""Tie isolated GND-pour islands to the plane, then re-fill.

The single-layer B.Cu fan can pinch a QSE ground pad into a tiny pour island cut off from
the main plane. This pass fills, finds every GND island on F.Cu/B.Cu that holds a pad but no
via, drops a small GND via inside it (nudged to the island's roomiest interior point so it
clears the pinching traces), and re-fills. Run AFTER import_ses + stitch, BEFORE the final DRC.

  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/tie_islands.py <board.kicad_pcb>
"""
import os
import sys
import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pinout  # noqa: E402

GND = pinout.GROUND_NET
TIE_DIA, TIE_DRILL = 0.6, 0.3   # board-standard via (0.15 mm annular); fits the pinched sliver


def MM(v):
    return pcbnew.FromMM(v)


def fill(board):
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def gnd_via(board, pt, net):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(int(pt[0]), int(pt[1])))
    v.SetDrill(MM(TIE_DRILL))
    v.SetWidth(MM(TIE_DIA))
    v.SetNet(net)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(v)


def untied_islands(board):
    """Return interior tie points for GND islands that hold a pad but no via."""
    vias = [v.GetPosition() for v in board.GetTracks() if isinstance(v, pcbnew.PCB_VIA)]
    tht = [p.GetPosition() for fp in board.GetFootprints() for p in fp.Pads()
           if p.GetNetname().endswith(GND) and p.GetDrillSize().x > 0]
    pads = [p.GetPosition() for fp in board.GetFootprints() for p in fp.Pads()
            if p.GetNetname().endswith(GND)]
    ties = []
    for z in board.Zones():
        if board.GetLayerName(z.GetLayer()) not in ("F.Cu", "B.Cu"):
            continue
        polys = z.GetFilledPolysList(z.GetLayer())
        for i in range(polys.OutlineCount()):
            ol = polys.Outline(i)
            xs = [ol.CPoint(k).x for k in range(ol.PointCount())]
            ys = [ol.CPoint(k).y for k in range(ol.PointCount())]
            bx = (min(xs), max(xs), min(ys), max(ys))

            def inside(p, bx=bx):
                return bx[0] <= p.x <= bx[1] and bx[2] <= p.y <= bx[3]

            if any(inside(v) for v in vias) or any(inside(p) for p in tht):
                continue                       # already plane-tied
            here = [p for p in pads if inside(p)]
            if not here:
                continue                       # floating sliver -> island removal drops it
            # tie at the pad, nudged along the island's long axis to the roomiest interior
            pad = here[0]
            cx = (bx[0] + bx[1]) / 2.0
            ties.append((cx if abs(bx[1] - bx[0]) > abs(bx[3] - bx[2]) else pad.x, pad.y))
    return ties


def main():
    path = sys.argv[1]
    board = pcbnew.LoadBoard(path)
    fill(board)
    net = board.FindNet(GND)
    if net is None:
        for fp in board.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname().endswith(GND):
                    net = p.GetNet()
                    break
            if net:
                break
    ties = untied_islands(board)
    for pt in ties:
        gnd_via(board, pt, net)
    fill(board)
    board.Save(path)
    print(f"tie_islands {os.path.basename(path)}: {len(ties)} GND ties added")


if __name__ == "__main__":
    main()
