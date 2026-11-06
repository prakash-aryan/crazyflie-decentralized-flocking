import threading
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

from config import DRONE_URIS, FORMATION_RADIUS, drone_id


def main():
    cflib.crtp.init_drivers(enable_debug_driver=False)
    armed = []
    for uri in DRONE_URIS:
        i = drone_id(uri)
        try:
            with SyncCrazyflie(uri, cf=Crazyflie(rw_cache="./cache")) as scf:
                scf.cf.param.set_value("flock.enable", 1)
                scf.cf.param.set_value("flock.form_r", FORMATION_RADIUS)
                time.sleep(0.2)
                stored = []
                for name in ("flock.enable", "flock.form_r"):
                    done = threading.Event()
                    scf.cf.param.persistent_store(name, lambda n, ok, s=stored, e=done: (s.append(ok), e.set()))
                    done.wait(3)
                armed.append(i)
                print(f"id{i}: flocking enabled, form_r={FORMATION_RADIUS}, stored on drone: {all(stored) and len(stored) == 2}")
        except Exception as exc:
            print(f"id{i}: unreachable ({exc})")
        time.sleep(0.15)
    print(f"\narmed: {armed}")


if __name__ == "__main__":
    main()
