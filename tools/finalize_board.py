#!/usr/bin/env python
"""Stackup + net classes + 50 ohm channel routing + GND pours + stitching.

Loads a placed board from gen_board.py and adds the electrical layer:
  - 4-layer stackup (L1 sig / L2 GND / L3 GND / L4 sig)
  - 50 ohm channel traces; each SIPM_Kx / IV pin -> its jack signal pad.
    Same-side nets (QSE pad column matches jack side) route on F.Cu; nets that
    cross (flange grouping interleaves the connector rows) route on B.Cu.
  - GND (GNDA) zones on all four layers; the F.Cu/B.Cu pours act as the guard
    around every signal trace. Zones are left UNFILLED here -> run fill_zones.py
    on the saved file (headless ZONE_FILLER segfaults in-memory; see CLAUDE.md).
  - perimeter GND stitching vias tying the planes together.

Run with KiCad's bundled python:
  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/finalize_board.py <board.kicad_pcb>
"""
import os
import sys
import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pinout  # noqa: E402

def MM(v): return pcbnew.FromMM(v)

TRACE_W = 0.34     # ~50 ohm microstrip, PCBWay default 4-layer (0.21mm prepreg, Dk~4.3)
CLEAR = 0.30       # trace-to-pour (limits coplanar coupling)
VIA_DIA, VIA_DRILL = 0.6, 0.3
GND = pinout.GROUND_NET
SIG_PAD, GND_PAD = "1", "2"


def track(board, a, b, layer, net, w=TRACE_W):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(a); t.SetEnd(b)
    t.SetWidth(MM(w)); t.SetLayer(layer); t.SetNet(net)
    board.Add(t)
    return t


def via(board, p, net):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(p)
    v.SetDrill(MM(VIA_DRILL)); v.SetWidth(MM(VIA_DIA))
    v.SetNet(net)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(v)
    return v


def setup_layers(board):
    board.SetCopperLayerCount(4)
    board.SetLayerName(pcbnew.In1_Cu, "GND1")
    board.SetLayerName(pcbnew.In2_Cu, "GND2")
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(4)
    # 0.8 mm QSE pitch -> mask webs are thinner than the default min; the fab
    # handles fine-pitch mask, so don't flag the slivers.
    try:
        ds.m_SolderMaskMinWidth = 0
    except Exception:
        pass


def channel_routes(board):
    """Escape each QSE pad horizontally past the connector, then a single straight
    segment to its jack. The QSE is mounted on the opposite PCB face from the
    jacks, so its pads sit on HOME (the QSE's own copper layer); same-side fans
    stay on HOME and nets that cross the connector (and IV, to the north jack) hop
    to OTHER (the other signal layer). Because each cluster's pins and jacks are
    both sorted by position, the straight segments are order-preserving and don't
    cross within a cluster."""
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    qse = fps["J5"]
    qse_by_net = {}
    for p in qse.Pads():
        qse_by_net.setdefault(p.GetNetname(), []).append(p)
    # the QSE is SMD on a single face; route its escapes on whatever layer it is
    # on (HOME) and reserve the other signal layer (OTHER) for the crossing fans.
    smd_qse = [p for p in qse.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
    # NB: pad.GetLayer() reports a misleading "primary" layer for a flipped SMD pad;
    # IsOnLayer() is the reliable test for which copper face the pad actually sits on.
    on_back = bool(smd_qse) and smd_qse[0].IsOnLayer(pcbnew.B_Cu)
    HOME = pcbnew.B_Cu if on_back else pcbnew.F_Cu
    OTHER = pcbnew.F_Cu if HOME == pcbnew.B_Cu else pcbnew.B_Cu
    jack_by_net = {}
    for ref, fp in fps.items():
        if ref == "J5" or ref.startswith("REF"):
            continue
        for p in fp.Pads():
            if p.GetPadName() == SIG_PAD and p.GetNetname():
                jack_by_net[p.GetNetname()] = p
    xs = [p.GetPosition().x for p in qse.Pads()]
    qleft, qright = min(xs), max(xs)
    cx, cy = qse.GetPosition().x, qse.GetPosition().y
    esc, appr = MM(2.0), MM(4.0)

    # collect routable nets with their QSE pad + jack pad
    nets = []
    for sig in pinout.BREAKOUT_SIGNALS:
        jp = next((p for nm, p in jack_by_net.items() if nm.endswith(sig)), None)
        qps = [p for nm, ps in qse_by_net.items() if nm.endswith(sig) for p in ps]
        if jp is None or not qps:
            continue
        jpos = jp.GetPosition()
        qp = min(qps, key=lambda p: (p.GetPosition() - jpos).EuclideanNorm())
        smd = jp.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
        nets.append((sig, jp.GetNet(), qp.GetPosition(), jpos, qps, smd))

    def classify(qpos, jpos):
        if abs(jpos.x - cx) < MM(3):
            return "north", OTHER
        jack_east = jpos.x > cx
        return ("east" if jack_east else "west"), \
               (HOME if (qpos.x > cx) == jack_east else OTHER)

    import collections
    groups = collections.defaultdict(list)
    for sig, net, qpos, jpos, qps, smd in nets:
        groups[classify(qpos, jpos)].append((net, qpos, jpos, qps, smd))

    for (edge, layer), grp in groups.items():
        grp.sort(key=lambda t: t[2].y)              # by jack y (monotonic fan)
        for r, (net, qpos, jpos, qps, smd) in enumerate(grp):
            # 1) escape clear of the connector pads on the QSE's own layer, then
            #    hop to OTHER for the crossing fans
            ex = (qright + esc) if qpos.x > cx else (qleft - esc)
            e0 = pcbnew.VECTOR2I(int(ex), qpos.y)
            track(board, qpos, e0, HOME, net)
            if layer != HOME:
                via(board, e0, net)
            # 2) one straight (monotonic -> planar) run to the jack-approach point,
            #    then straight into the signal pad between the grounds
            if edge == "north":
                ay = jpos.y + (appr if cy > jpos.y else -appr)
                apos = pcbnew.VECTOR2I(jpos.x, int(ay))
            else:
                ax = jpos.x + (appr if cx > jpos.x else -appr)
                apos = pcbnew.VECTOR2I(int(ax), jpos.y)
            track(board, e0, apos, layer, net)
            if layer == pcbnew.B_Cu and smd:
                # SMD jack pad is F.Cu-only: pop a B.Cu run back up at the jack
                via(board, apos, net)
                track(board, apos, jpos, pcbnew.F_Cu, net)
            else:
                track(board, apos, jpos, layer, net)
            # tie any extra QSE pads on this net (e.g. IV spans pins 40 & 42)
            for extra in qps:
                if extra.GetPosition() != qpos:
                    track(board, qpos, extra.GetPosition(), HOME, net)


def gnd_zones(board):
    gnet = board.FindNet(GND) or board.FindNet(f"/Channels/{GND}")
    if gnet is None:
        # GNDA may be stored unscoped; grab from a QSE GND pad
        for fp in board.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname().endswith(GND):
                    gnet = p.GetNet(); break
            if gnet: break
    bb = board.GetBoardEdgesBoundingBox()
    x1, y1, x2, y2 = bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()
    for layer in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnet)
        z.SetLocalClearance(MM(CLEAR))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)  # solid GND (RF) -> no thermal starve
        z.SetIsFilled(False)
        pts = pcbnew.VECTOR_VECTOR2I()
        for x, y in [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]:
            pts.append(pcbnew.VECTOR2I(x, y))
        z.AddPolygon(pts)
        board.Add(z)
    return gnet


def stitching(board, gnet):
    # keep stitching vias away from drilled holes (mounting holes etc.)
    holes = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetDrillSize().x > 0:
                holes.append(p.GetPosition())
    def clear(pt):
        return all((pt - h).EuclideanNorm() > MM(3.5) for h in holes)
    bb = board.GetBoardEdgesBoundingBox()
    step = MM(6)
    x = bb.GetLeft() + MM(3)
    while x < bb.GetRight() - MM(3):
        for y in (bb.GetTop() + MM(3), bb.GetBottom() - MM(3)):
            pt = pcbnew.VECTOR2I(int(x), int(y))
            if clear(pt):
                via(board, pt, gnet)
        x += step


def main():
    path = sys.argv[1]
    board = pcbnew.LoadBoard(path)
    setup_layers(board)
    channel_routes(board)
    gnet = gnd_zones(board)
    stitching(board, gnet)
    board.Save(path)
    print(f"finalized {os.path.basename(path)}: "
          f"{len(list(board.GetTracks()))} track/via objs, "
          f"{len(list(board.Zones()))} zones")


if __name__ == "__main__":
    main()
