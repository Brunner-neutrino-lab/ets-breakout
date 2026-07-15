#!/usr/bin/env python
"""Electrical setup, GND pours and stitching for an ETS breakout board.

Board A (MCX) is routed with FreeRouting (KiCad -> .dsn -> autoroute -> .ses -> KiCad),
so this script is split into pre-route and post-route passes; the SMD variants (B/C/D)
still use the built-in deterministic router via the legacy all-in-one mode.

Modes:
  finalize_board.py <pcb> setup   4-layer stackup + 50 ohm netclass width + GND zones
                                   (unfilled). Run BEFORE export_dsn.py so the DSN carries
                                   the trace width and FreeRouting only routes the 25 signals.
  finalize_board.py <pcb> stitch   perimeter GND stitching vias. Run AFTER import_ses.py.
  finalize_board.py <pcb>          legacy all-in-one: stackup + deterministic 50 ohm route +
                                   GND zones + stitching (SMD variants B/C/D, not autorouted).

Then fill_zones.py fills the pours (separate pass; headless ZONE_FILLER segfaults in-memory,
see CLAUDE.md). Stackup is L1 sig / L2 GND / L3 GND / L4 sig; the F.Cu/B.Cu GND pours guard
every signal trace.

Run with KiCad's bundled python:
  "C:/Program Files/KiCad/10.0/bin/python.exe" tools/finalize_board.py <board.kicad_pcb> [mode]
"""
import os
import sys
import json
import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pinout  # noqa: E402

def MM(v): return pcbnew.FromMM(v)

TRACE_W = 0.325    # ~50 ohm microstrip on the JLCPCB JLC04161H-7628 4-layer stack (0.2104 mm
                   # 7628 prepreg to the adjacent inner GND plane, Dk 4.4). Order as controlled
                   # impedance so JLC re-tunes the etched width to their measured stackup.
CLEAR = 0.30       # trace-to-pour (limits coplanar coupling)
VIA_DIA, VIA_DRILL = 0.6, 0.3
GND = pinout.GROUND_NET
SIG_PAD, GND_PAD = "1", "2"


def set_netclass_width(pcb_path):
    """Write the 50 ohm trace width into the sibling .kicad_pro Default netclass, so the
    Specctra DSN export carries it and FreeRouting routes at the impedance-controlled width."""
    pro = os.path.splitext(pcb_path)[0] + ".kicad_pro"
    if not os.path.exists(pro):
        return
    d = json.load(open(pro, encoding="utf-8"))
    for c in d.get("net_settings", {}).get("classes", []):
        if c.get("name") == "Default":
            c["track_width"] = TRACE_W
            c["clearance"] = 0.2
    json.dump(d, open(pro, "w", encoding="utf-8"), indent=2)


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
        # single-layer signal routing fragments the B.Cu pour; drop floating slivers so they
        # aren't flagged as unconnected GND islands (the In1/In2 planes carry the real GND).
        try:
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        except AttributeError:
            z.SetIslandRemovalMode(0)
        z.SetIsFilled(False)
        pts = pcbnew.VECTOR_VECTOR2I()
        for x, y in [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]:
            pts.append(pcbnew.VECTOR2I(x, y))
        z.AddPolygon(pts)
        board.Add(z)
    return gnet


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    cx, cy = ax + t * dx, ay + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def stitching(board, gnet):
    """Grid of GND vias tying the F.Cu/B.Cu pours to the In1/In2 planes. A full grid (not
    just the perimeter) is needed because the single-layer B.Cu fan pinches the pour into
    regions -- notably the QSE's own ground pads at board centre -- that each need a plane
    tie. Vias are dropped only where they clear signal pads, drilled holes and signal tracks."""
    sig_pads, holes = [], []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetDrillSize().x > 0:
                holes.append(p.GetPosition())
            if not p.GetNetname().endswith(GND):
                sig_pads.append(p.GetPosition())
    sig_segs = [t for t in board.GetTracks()
                if isinstance(t, pcbnew.PCB_TRACK) and not isinstance(t, pcbnew.PCB_VIA)
                and not t.GetNetname().endswith(GND)]

    def clear(pt):
        if any((pt - h).EuclideanNorm() <= MM(3.5) for h in holes):
            return False
        if any((pt - q).EuclideanNorm() <= MM(1.0) for q in sig_pads):
            return False
        px, py = pt.x, pt.y
        for t in sig_segs:
            a, b = t.GetStart(), t.GetEnd()
            if _seg_dist(px, py, a.x, a.y, b.x, b.y) <= MM(0.8):
                return False
        return True

    bb = board.GetBoardEdgesBoundingBox()
    step = MM(5)
    y = bb.GetTop() + MM(3)
    n = 0
    while y < bb.GetBottom() - MM(3):
        x = bb.GetLeft() + MM(3)
        while x < bb.GetRight() - MM(3):
            pt = pcbnew.VECTOR2I(int(x), int(y))
            if clear(pt):
                via(board, pt, gnet)
                n += 1
            x += step
        y += step
    return n


def _find_gnd(board):
    gnet = board.FindNet(GND) or board.FindNet(f"/Channels/{GND}")
    if gnet is None:
        for fp in board.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname().endswith(GND):
                    return p.GetNet()
    return gnet


def main():
    path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "full"
    board = pcbnew.LoadBoard(path)
    if mode in ("setup", "full"):
        setup_layers(board)
    if mode == "full":                      # deterministic router (SMD variants B/C/D)
        channel_routes(board)
    gnet = None
    if mode in ("setup", "full"):
        gnet = gnd_zones(board)             # unfilled; fill_zones.py fills after routing
    if mode in ("stitch", "full"):
        stitching(board, gnet or _find_gnd(board))
    board.Save(path)
    if mode in ("setup", "full"):
        set_netclass_width(path)
    print(f"finalize[{mode}] {os.path.basename(path)}: "
          f"{len(list(board.GetTracks()))} track/via objs, "
          f"{len(list(board.Zones()))} zones")


if __name__ == "__main__":
    main()
