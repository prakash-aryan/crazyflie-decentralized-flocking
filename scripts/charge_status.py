"""Report battery voltage and charge state for every drone.

A drone below TAKEOFF_VOLTAGE will not lift off, so run this before flying.
"""
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger

from config import DRONE_URIS, TAKEOFF_VOLTAGE, drone_id

PM_STATE = {0: "on battery", 1: "charging", 2: "charged", 3: "low power", 4: "shutdown"}


def main():
    cflib.crtp.init_drivers(enable_debug_driver=False)
    ready = 0
    for uri in DRONE_URIS:
        i = drone_id(uri)
        try:
            with SyncCrazyflie(uri, cf=Crazyflie(rw_cache="./cache")) as scf:
                lg = LogConfig(name="bat", period_in_ms=200)
                lg.add_variable("pm.vbat", "float")
                lg.add_variable("pm.state", "uint8_t")
                with SyncLogger(scf, lg) as logger:
                    for entry in logger:
                        vbat = entry[1]["pm.vbat"]
                        state = entry[1]["pm.state"]
                        break
                flyable = vbat >= TAKEOFF_VOLTAGE
                ready += flyable
                mark = "FLYABLE" if flyable else "below takeoff voltage"
                print(f"id{i}: {vbat:.2f}V  {PM_STATE.get(state, state):11s}  {mark}")
        except Exception as exc:
            print(f"id{i}: unreachable ({exc})")
        time.sleep(0.2)
    print(f"\n{ready}/{len(DRONE_URIS)} ready to fly")


if __name__ == "__main__":
    main()
