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
# style "edge" = right-angle jack, cable exits sideways (rotate exit->edge normal).
# style "flat" = vertical SMD jack, cable exits perpendicular (off the board face).
VARIANTS = {
    # straight (vertical) THROUGH-HOLE MCX jack (MCX-J-P-H-ST-TH1): signal pin is plated
    # through all layers, so the QSE B.Cu channel escape lands directly on it with NO
    # face-change via. Centered signal pad -> orientation-independent. style "tht" places
    # it like a flat jack (cable exits up) but its through-hole pad needs no jack-side via.
    "mcx": dict(fp="Samtec_MCX-J-P-H-ST-TH1",           exit=(0, 1),  pitch=8.0, style="tht"),
    "sma": dict(fp="SMA_Amphenol_901-143_Horizontal",   exit=(0, -1), pitch=10.0, style="edge"),
    "ufl": dict(fp="U.FL_Hirose_U.FL-R-SMT-1_Vertical",  exit=(0, 1),  pitch=6.0, style="flat"),
    # SMP vertical SMD (Amphenol SMP-MSLD-PCS-20): signal is an external tab on one
    # side of the body, so it routes like U.FL (smd) once the jack is rotated to face
    # its tab toward the QSE -- _edge does that. Body ~7 mm across -> 8 mm pitch.
    "smp": dict(fp="SMP_Amphenol_SMP-MSLD-PCS-20",       exit=(0, 1),  pitch=8.0, style="flat"),
}

EDGE_GAP = 26.0    # mm QSE edge -> jack column; long run keeps the fan diagonals
                   # shallow enough that 50-ohm-width traces clear at the dense escape
STAGGER = 0.0      # single column per edge (order-preserving fan routes cleanly)

# Jack-to-edge assignment. The QSE-040's two pin rows split the 24 channels 8 (west,
# the odd-pin row K8-K15) / 16 (east, K0-K7 + K16-K23); IV is in the east row.
#   "balanced" -> balance the two edges ~12/13 for a compact, symmetric board. Each edge's
#                 jacks are ordered by their QSE pin so every native route is a straight
#                 line; the surplus of the larger (east) column spills its END-most channels
#                 (K4-K7) onto the west edge, where they WRAP around the connector end on
#                 B.Cu (FreeRouting, single signal layer -> still ZERO signal vias). This is
#                 the engineer-reviewed layout (2026-07-17).
#   "planar"   -> each jack on the edge matching its own QSE pin column: monotonic single-
#                 layer fan, zero wrap, but lopsided edge counts 8 / 16+IV.
SPLIT = "balanced"
EDGE_NORMAL = {"west": (-1, 0), "east": (1, 0), "north": (0, -1), "south": (0, 1)}


def short(sig):
    return sig.replace("SIPM_", "")


def jack_ref(sig):
    """Reference designator for a coax jack. Jacks are connectors -> 'J' (not 'K', which is a
    relay). The detector socket keeps J5 (upstream mapping), so jacks are J6..J30: K0->J6 ...
    K23->J29, IV->J30. The channel identity (K0..K23, IV) goes on the silkscreen next to the jack."""
    if sig == "IV":
        return "J30"
    return "J%d" % (6 + int(sig.replace("SIPM_K", "")))


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
        # Mount the QSE on the opposite PCB face from the coax jacks: the detector
        # plugs into the back, cables come off the front. Flip top<->bottom (mirror
        # Y) so the pin columns stay on their sides; pad->net binding is preserved.
        qse.Flip(qse.GetPosition(), False)

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

        # Assign each channel's jack to a board edge from real QSE geometry, in QSE-pin
        # (pad-y) order so every native route is a straight line.
        ch = [f"SIPM_K{i}" for i in range(24)]
        yk = lambda s: self.padpos[s][1]
        west_col = sorted([s for s in ch if self.padpos[s][0] < self.cx], key=yk)
        east_col = sorted([s for s in ch if self.padpos[s][0] > self.cx], key=yk)
        iv_side = "east" if self.padpos["IV"][0] > self.cx else "west"
        if SPLIT == "balanced":
            # spill the larger column's surplus to the small edge, split between its TWO ends
            # so the wraps form only ~2 concentric arcs per connector corner (4 around one
            # corner is too tight to route on a single layer). Native jacks stay in pin order
            # (straight); the top-spill wraps the top corner, the bottom-spill the bottom.
            big, big_side, small, small_side = (
                (east_col, "east", west_col, "west") if len(east_col) >= len(west_col)
                else (west_col, "west", east_col, "east"))
            n = (len(big) - len(small)) // 2                     # 4 -> 12 small / 12 big (+IV)
            nt, nb = n // 2, n - n // 2                          # 2 top-corner, 2 bottom-corner
            top_spill = big[:nt]
            bot_spill = big[len(big) - nb:]
            big_keep = big[nt:len(big) - nb]
            clusters = {big_side: sorted(big_keep, key=yk), small_side: sorted(small, key=yk)}
            # IV inline on its native edge, at its pin-y rank (still a straight route)
            clusters[iv_side] = sorted(clusters[iv_side] + ["IV"], key=yk)
            # small edge, top->bottom: top-corner wraps, native fan (pin order), bottom wraps
            clusters[small_side] = (sorted(top_spill, key=yk) + clusters[small_side]
                                    + sorted(bot_spill, key=yk))
            self.clusters = clusters
        else:  # "planar": each jack on its own pin column's edge (lopsided, zero wrap)
            self.clusters = {"west": west_col, "east": east_col}
            self.clusters[iv_side] = sorted(self.clusters[iv_side] + ["IV"], key=yk)
        for side in ("west", "east"):
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
        # sigs arrive pre-ordered from build() (native jacks in pin order, then wrapped ones);
        # preserve that order so native routes stay straight and wrapped ones tuck in at the end
        flat = self.cfg["style"] != "edge"
        rot = 0.0 if flat else self.rot_to(self.cfg["exit"], normal)
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
            fp = self.add_fp(LIB, self.cfg["fp"], jack_ref(sig), x, y, rot)
            if flat:
                self._face_signal_to_qse(fp, side)  # aim the signal pad inward
            self.pad_net(fp, SIG_PAD, sig)
            self.pad_net(fp, GND_PAD, GND_NET)
            self._channel_label(short(sig), x, y, side, horiz)

    def _channel_label(self, text, x, y, side, horiz):
        """Silk channel indicator (K0..K23 / IV) just inboard of the jack, toward the QSE,
        clear of the jack pads and its neighbours (the ref designator J.. sits on the far side)."""
        off = 5.5
        if horiz:
            tx, ty = x, y - off * EDGE_NORMAL[side][1]
        else:
            tx, ty = x - off * EDGE_NORMAL[side][0], y
        t = pcbnew.PCB_TEXT(self.board)
        t.SetText(text)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetPosition(V(tx, ty))
        t.SetTextSize(pcbnew.VECTOR2I(MM(1.2), MM(1.2)))
        t.SetTextThickness(MM(0.2))
        self.board.Add(t)

    def _sig_local(self, fp):
        """Signal pad offset from the footprint origin (board units), as (dx, dy)."""
        o = fp.GetPosition()
        for p in fp.Pads():
            if p.GetPadName() == SIG_PAD:
                pp = p.GetPosition()
                return pp.x - o.x, pp.y - o.y
        return 0, 0

    def _face_signal_to_qse(self, fp, side):
        """Rotate a flat (vertical) jack so its signal pad points inward toward the
        QSE -- the side the channel trace approaches from. Whatever direction the pad
        sits in the footprint's own frame (U.FL: -X edge; SMP-MSLD: +Y tab), this aims
        it at +X (west cluster) / -X (east cluster). Centre-pad parts (MCX) have no
        preferred direction, so they keep the legacy orientation."""
        vx, vy = self._sig_local(fp)
        if vx * vx + vy * vy < MM(0.2) ** 2:        # signal pad ~centred (MCX)
            fp.SetOrientationDegrees(180.0 if side == "west" else 0.0)
            return
        inward = 1.0 if side == "west" else -1.0    # +X toward QSE for west, -X for east
        native = math.degrees(math.atan2(vy, vx))
        want = 0.0 if side == "west" else 180.0
        # pcbnew's rotation sign vs screen Y is fiddly; try both signs and keep the
        # one that actually lands the pad on the inward side.
        best_deg, best_score = 0.0, -1e18
        for cand in (want - native, native - want):
            fp.SetOrientationDegrees(cand)
            sx, _ = self._sig_local(fp)
            score = sx * inward
            if score > best_score:
                best_deg, best_score = cand, score
        fp.SetOrientationDegrees(best_deg)

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
            mh.Reference().SetVisible(False)   # designator not wanted on silk (engineer note)
            mh.SetPosition(pcbnew.VECTOR2I(int(hx), int(hy)))


def main():
    which = (sys.argv[1] if len(sys.argv) > 1 else "all").lower()
    todo = list(VARIANTS) if which == "all" else [which]
    letter = {"mcx": "A", "sma": "B", "ufl": "C", "smp": "D"}
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
