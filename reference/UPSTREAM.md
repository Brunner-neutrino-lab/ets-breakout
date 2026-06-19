# Upstream reference — ETS-96-channel-IV-pulse-mux

`ETS-96-channel-IV-pulse-mux/` is a **read-only snapshot** of the Brunner-lab
multiplexer project. It is the source from which the authoritative QSE-040 (J5)
pin → net map in [`../pinout.py`](../pinout.py) was extracted (via
`kicad-cli sch export netlist`, not hand-transcribed). It is kept here for
provenance only — **do not edit it; do not build from it.**

| | |
|---|---|
| Origin | <https://github.com/Brunner-neutrino-lab/ETS-96-channel-IV-pulse-mux.git> |
| Commit | `757c28fd36a7ed9862af2c0177549747f3e05412` (`757c28f`) |
| Board / connector of interest | `iv-pulse-mux` board, connector **J5** (QSE-040-01-L-D-A) |

The clone's own `.git` was removed during the repo reorganization so this does
not nest a second git repository inside `ets-breakout`. To refresh the snapshot,
re-clone from the URL above at the desired commit.

> Note: the public GitHub repo `IV-MUX-public` is a *different, older* board
> (15 ch/board relay mux) — do not conflate it with this one.
