"""Fly the swarm through flock, circle, line, then land.

    python formation_demo.py 6

Everything goes through the sniffer as a single P2P broadcast: the desired flying count
and the formation mode. No per-drone radio link is opened while the drones are airborne.
Opening unicast links to each drone mid-flight will saturate a single Crazyradio and can
stall the script, which is why the mode is broadcast instead.

The swarm always lands on exit, including on Ctrl-C or an error.
"""
import sys
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

from config import SNIFFER_URI

FLOCK, CIRCLE, LINE = 0, 1, 2

TAKEOFF_HOLD = 14   # seconds, long enough for every drone to reach altitude
CIRCLE_HOLD = 22
LINE_HOLD = 22
FLOCK_HOLD = 8
LAND_HOLD = 12

_console = {"buffer": ""}


def on_console(text):
    _console["buffer"] += text
    while "\n" in _console["buffer"]:
        line, _console["buffer"] = _console["buffer"].split("\n", 1)
        line = line.strip()
        if line:
            print("  [sniffer]", line, flush=True)


def set_desired(scf, count):
    scf.cf.param.set_value("app.zero", 1)
    time.sleep(0.3)
    for _ in range(count):
        scf.cf.param.set_value("app.more", 1)
        time.sleep(0.25)


def set_mode(scf, mode, label, hold):
    print(f"\n>>> {label} (broadcast app.mode={mode})", flush=True)
    scf.cf.param.set_value("app.mode", mode)
    for _ in range(hold):
        time.sleep(1)


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    cflib.crtp.init_drivers(enable_debug_driver=False)

    with SyncCrazyflie(SNIFFER_URI, cf=Crazyflie(rw_cache="./cache")) as scf:
        scf.cf.console.receivedChar.add_callback(on_console)
        time.sleep(1)
        try:
            print(f">>> taking off, desired = {count}", flush=True)
            scf.cf.param.set_value("app.mode", FLOCK)
            set_desired(scf, count)
            for _ in range(TAKEOFF_HOLD):
                time.sleep(1)

            set_mode(scf, CIRCLE, "circle", CIRCLE_HOLD)
            set_mode(scf, LINE, "line", LINE_HOLD)
            set_mode(scf, FLOCK, "back to flock", FLOCK_HOLD)
        finally:
            print("\n>>> landing", flush=True)
            try:
                scf.cf.param.set_value("app.mode", FLOCK)
                set_desired(scf, 0)
            except Exception as exc:
                print("could not send land command:", exc, flush=True)
            for _ in range(LAND_HOLD):
                time.sleep(1)
            print(">>> done", flush=True)


if __name__ == "__main__":
    main()
