"""Sanity + self-consistency checks for the QSE-040 (J5) breakout pinout.

Run: python ets-breakout/tests/test_pinout.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pinout  # noqa: E402


def test_breakout_count():
    assert len(pinout.BREAKOUT_SIGNALS) == 25, "24 SiPM channels + IV"
    assert len(set(pinout.BREAKOUT_SIGNALS)) == 25, "no duplicate jacks"


def test_all_sipm_channels_present_once():
    for i in range(24):
        pins = pinout.net_to_pins(f"SIPM_K{i}")
        assert len(pins) == 1, f"SIPM_K{i} should map to exactly one pin, got {pins}"


def test_iv_spans_two_pins():
    assert pinout.net_to_pins("IV") == [40, 42], "IV is bussed across pins 40 and 42"


def test_excluded_thermistors():
    assert pinout.net_to_pins("THERM4") == [77]
    assert pinout.net_to_pins("THERM5") == [79]
    for t in pinout.EXCLUDED_SIGNALS:
        assert t not in pinout.BREAKOUT_SIGNALS


def test_no_pin_serves_two_breakout_signals():
    seen = {}
    for sig, pins in pinout.breakout_map().items():
        for p in pins:
            assert p not in seen, f"pin {p} claimed by {seen.get(p)} and {sig}"
            seen[p] = sig


def test_pin_accounting():
    pins = pinout.J5_PINOUT
    assert len(pins) == 88, "80 signal contacts + 8 G-pads"
    signal_contacts = [p for p in pins if isinstance(p, int)]
    assert sorted(signal_contacts) == list(range(1, 81))
    non_ground = [p for p, n in pins.items() if n != pinout.GROUND_NET]
    # 24 SiPM + 2 IV pins + 2 THERM = 28 non-ground contacts
    assert len(non_ground) == 28, f"expected 28 non-ground contacts, got {len(non_ground)}"
    assert len(pinout.net_to_pins(pinout.GROUND_NET)) == 88 - 28 == 60


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                failures += 1
                print(f"FAIL {name}: {e}")
    print(f"\n{'ALL PASSED' if not failures else str(failures) + ' FAILED'}")
    sys.exit(1 if failures else 0)
