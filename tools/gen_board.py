#!/usr/bin/env python
"""Generate an ETS per-channel breakout board: placement + nets + outline + holes.

Single source of truth for the pinout is ../pinout.py. Connectors are never
hand-placed: this script reads the QSE-040 (J5) pin->net map and fans each
SIPM_Kx / IV pin out to its own coax jack, staggered along the top & bottom
edges, ordered by the pin's X position so the fan-out doesn't cross.

Routing and GND pours are applied in later passes (see fill_zones / route steps),
per the pcbnew gotchas in CLAUDE.md (headless ZONE_FILLER segfaults in-memory).

Run with KiCad's bundled python:
  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/gen_board.py [mcx|sma|ufl|all]
"""
import os
import sys
import math
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import pinout  # noqa: E402

def MM(v):   return pcbnew.FromMM(v)
def V(x, y): return pcbnew.VECTOR2I(MM(x), MM(y))

LIB = os.path.join(ROOT, "lib", "ets-breakout.pretty")
KICAD_FP = r"C:/Program Files/KiCad/10.0/share/kicad/footprints"
MOUNT_LIB = os.path.join(KICAD_FP, "MountingHole.pretty")
QSE_FP = "SAMTEC_QSE-040-01-X-D-A"
GND_NET = pinout.GROUND_NET
SIG_PAD, GND_PAD = "1", "2"

# native cable-exit unit vector per footprint, edge jack pitch (mm), placement style
VARIANTS = {
    "mcx": dict(fp="Samtec_MCX-J-P-H-RA-TH1",            exit=(-1, 0), pitch=9.0, style="edge"),
    "sma": dict(fp="SMA_Amphenol_901-143_Horizontal",   exit=(0, -1), pitch=10.0, style="edge"),
    "ufl": dict(fp="U.FL_Hirose_U.FL-R-SMT-1_Vertical",  exit=(0, 1),  pitch=6.0, style="flat"),
}

EDGE_GAP = 26.0    # mm QSE edge -> jack column; long run keeps the fan diagonals
                   # shallow enough that 50-ohm-width traces clear at the dense escape
STAGGER = 0.0      # single column per edge (order-preserving fan routes cleanly)

# Flange grouping: each cluster of jacks bundles to one vacuum feedthrough flange.
# 12 K-channels -> flange 1 (west), 12 -> flange 2 (east), IV -> flange 3 (north).
# Split chosen (flexible per Lucas) to align with the QSE pin rows: the odd-pin row
# carries K8-K15 (8) and the even-pin row K0-K7 + K16-K23 (16). Putting all 8 odd
# (K8-K15) + K0-K3 on the west cluster and the rest east leaves only K0-K3 crossing
# the connector (routed on the bottom layer) -- the theoretical minimum for 12/12.
WEST = [f"SIPM_K{i}" for i in (0, 1, 2, 3, 8, 9, 10, 11, 12, 13, 14, 15)]
EAST = [f"SIPM_K{i}" for i in (4, 5, 6, 7, 16, 17, 18, 19, 20, 21, 22, 23)]
GROUPS = [
    ("west",  WEST),     # flange 1
    ("east",  EAST),     # flange 2
    ("north", ["IV"]),   # flange 3
]
EDGE_NORMAL = {"west": (-1, 0), "east": (1, 0), "north": (0, -1), "south": (0, 1)}


def short(sig):
    return sig.replace("SIPM_", "")


class Builder:
    def __init__(self, variant):
        self.variant = variant
        self.cfg = VARIANTS[variant]
        self.board = pcbnew.BOARD()
        self.board.SetCopperLayerCount(4)
        self.nets = {}

    def net(self, name):
        if name not in self.nets:
            n = pcbnew.NETINFO_ITEM(self.board, name)
            self.board.Add(n)
            self.nets[name] = n
        return self.nets[name]

    def add_fp(self, lib, name, ref, x, y, rot=0.0):
        fp = pcbnew.FootprintLoad(lib, name)
        self.board.Add(fp)
        fp.SetReference(ref)
        fp.SetPosition(V(x, y))
        if rot:
            fp.SetOrientationDegrees(rot)
        return fp

    def pad_net(self, fp, padname, netname):
        net = self.net(netname)
        for p in fp.Pads():
            if p.GetPadName() == padname:
                p.SetNet(net)

    def rot_to(self, exitv, normal):
        return math.degrees(math.atan2(normal[1], normal[0]) -
                            math.atan2(exitv[1], exitv[0]))

    def build(self):
        # --- QSE-040 centered, vertical (long axis Y) so the two pin rows face
        #     the west/east flange clusters ---
        qse = self.add_fp(LIB, QSE_FP, "J5", 0, 0, 90)
        for pin, netname in pinout.J5_PINOUT.items():
            padname = f"{pin:02d}" if isinstance(pin, int) else pin
            self.pad_net(qse, padname, netname)

        # mean (x,y) of each broken-out signal's QSE pin(s), and QSE pad extents
        pp = {}
        xs, ys = [], []
        for p in qse.Pads():
            pos = p.GetPosition()
            pp.setdefault(p.GetPadName(), []).append((pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)))
            xs.append(pcbnew.ToMM(pos.x)); ys.append(pcbnew.ToMM(pos.y))
        self.padpos = {}
        for sig in pinout.BREAKOUT_SIGNALS:
            pts = [pp[f"{q:02d}"][0] for q in pinout.net_to_pins(sig)]
            self.padpos[sig] = (sum(a for a, _ in pts) / len(pts),
                                sum(b for _, b in pts) / len(pts))
        self.qse_ext = dict(left=min(xs), right=max(xs), top=min(ys), bottom=max(ys))
        self.cx = qse.GetPosition().x

        # Choose the 12/12 flange split from real geometry to minimise crossings:
        # each channel sits in the west or east pin column; give each edge cluster
        # its own column's channels, and spill the larger column's surplus to the
        # other edge (those few cross on the bottom layer).
        ch = [f"SIPM_K{i}" for i in range(24)]
        west_col = sorted([s for s in ch if self.padpos[s][0] < self.cx],
                          key=lambda s: self.padpos[s][1])
        east_col = sorted([s for s in ch if self.padpos[s][0] > self.cx],
                          key=lambda s: self.padpos[s][1])
        big, big_side, small, small_side = (
            (west_col, "west", east_col, "east") if len(west_col) >= len(east_col)
            else (east_col, "east", west_col, "west"))
        need = 12 - len(small)
        yc = sum(self.padpos[s][1] for s in small) / len(small)
        spill = sorted(big, key=lambda s: abs(self.padpos[s][1] - yc))[:need]
        small_cluster = sorted(small + spill, key=lambda s: self.padpos[s][1])
        big_cluster = sorted([s for s in big if s not in spill],
                             key=lambda s: self.padpos[s][1])
        self.clusters = {big_side: big_cluster, small_side: small_cluster}
        # IV (flange 3) routes cleanly inline on the edge matching its pin column,
        # slotted at its natural pin-y rank; still a separate connector to cable out.
        iv_side = "east" if self.padpos["IV"][0] > self.cx else "west"
        self.clusters[iv_side] = self.clusters[iv_side] + ["IV"]
        for side in (big_side, small_side):
            self._edge(self.clusters[side], side)

        self._outline_and_holes()
        self._recenter()
        return self.board

    def _recenter(self, margin=15.0):
        # shift everything into positive coords so it plots on-page
        xs, ys = [], []
        for fp in self.board.GetFootprints():
            for p in fp.Pads():
                pos = p.GetPosition()
                xs.append(pos.x); ys.append(pos.y)
        off = pcbnew.VECTOR2I(MM(margin) - min(xs), MM(margin) - min(ys))
        for fp in self.board.GetFootprints():
            fp.Move(off)
        for d in self.board.GetDrawings():
            d.Move(off)

    def _edge(self, sigs, side):
        """Place a flange-group cluster of jacks along one board edge."""
        normal = EDGE_NORMAL[side]
        pitch = self.cfg["pitch"]
        horiz = side in ("north", "south")          # step along X (else along Y)
        # order within the cluster by the pin coordinate to reduce crossing
        sigs = sorted(sigs, key=lambda s: self.padpos[s][0 if horiz else 1])
        if self.cfg["style"] == "edge":
            rot = self.rot_to(self.cfg["exit"], normal)
        else:
            # flat (U.FL): point the signal pad toward the QSE so the trace
            # approaches it from the open side, clear of the U.FL keepout
            rot = 180.0 if side == "west" else 0.0
        e = self.qse_ext
        base = {"west": e["left"] - EDGE_GAP, "east": e["right"] + EDGE_GAP,
                "north": e["top"] - EDGE_GAP, "south": e["bottom"] + EDGE_GAP}[side]
        span0 = -(len(sigs) - 1) * pitch / 2.0
        for i, sig in enumerate(sigs):
            stag = (i % 2) * STAGGER
            if horiz:
                x = span0 + i * pitch
                y = base + normal[1] * stag         # stagger alternate row outward
            else:
                y = span0 + i * pitch
                x = base + normal[0] * stag
            fp = self.add_fp(LIB, self.cfg["fp"], short(sig), x, y, rot)
            self.pad_net(fp, SIG_PAD, sig)
            self.pad_net(fp, GND_PAD, GND_NET)

    def _outline_and_holes(self):
        # extents from pad positions (reliable) + margin -> rectangular Edge.Cuts.
        # Edge jacks fill the W/E perimeter, so leave extra top/bottom room and put
        # the M3 holes in those clear margins, aligned to the jack columns.
        xs, ys, jxs = [], [], []
        for fp in self.board.GetFootprints():
            isj = fp.GetReference() != "J5"
            for p in fp.Pads():
                pos = p.GetPosition()
                xs.append(pos.x); ys.append(pos.y)
                if isj and p.GetPadName() == SIG_PAD:
                    jxs.append(pos.x)
        mx, my = MM(6.0), MM(12.0)
        x1, y1 = min(xs) - mx, min(ys) - my
        x2, y2 = max(xs) + mx, max(ys) + my
        for a, b in [((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)),
                     ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))]:
            seg = pcbnew.PCB_SHAPE(self.board)
            seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
            seg.SetStart(pcbnew.VECTOR2I(*a))
            seg.SetEnd(pcbnew.VECTOR2I(*b))
            seg.SetLayer(pcbnew.Edge_Cuts)
            seg.SetWidth(MM(0.15))
            self.board.Add(seg)
        westx, eastx = min(jxs), max(jxs)
        yt, yb = min(ys) - MM(7.0), max(ys) + MM(7.0)   # in the clear margins
        for i, (hx, hy) in enumerate([(westx, yt), (eastx, yt), (westx, yb), (eastx, yb)], 1):
            mh = pcbnew.FootprintLoad(MOUNT_LIB, "MountingHole_3.2mm_M3")
            self.board.Add(mh)
            mh.SetReference(f"MH{i}")
            mh.SetPosition(pcbnew.VECTOR2I(int(hx), int(hy)))


def main():
    which = (sys.argv[1] if len(sys.argv) > 1 else "all").lower()
    todo = list(VARIANTS) if which == "all" else [which]
    letter = {"mcx": "A", "sma": "B", "ufl": "C"}
    for v in todo:
        b = Builder(v).build()
        outdir = os.path.join(ROOT, "boards", f"board-{letter[v]}-{v}")
        os.makedirs(outdir, exist_ok=True)
        out = os.path.join(outdir, f"board-{letter[v]}-{v}.kicad_pcb")
        b.Save(out)
        nfp = len(list(b.GetFootprints()))
        print(f"[{v}] {nfp} footprints -> {out}")


if __name__ == "__main__":
    main()
