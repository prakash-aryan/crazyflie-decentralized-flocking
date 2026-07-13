"""Set how many drones should be flying, via the sniffer.

    python sniffer_ctl.py 6     take off until 6 drones are airborne
    python sniffer_ctl.py 0     land everything (use this as the stop command)

The sniffer broadcasts the desired count over P2P. The drones decide among themselves
who takes off and who lands, so this is the only command channel into the swarm.
"""
import sys
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

from config import SNIFFER_URI


def set_desired(scf, count):
    # The sniffer has no absolute "set" parameter, so reset to zero and increment.
    scf.cf.param.set_value("app.zero", 1)
    time.sleep(0.3)
    for _ in range(count):
        scf.cf.param.set_value("app.more", 1)
        time.sleep(0.25)


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    cflib.crtp.init_drivers(enable_debug_driver=False)
    with SyncCrazyflie(SNIFFER_URI, cf=Crazyflie(rw_cache="./cache")) as scf:
        set_desired(scf, count)
        print(f"broadcast desired flying drones = {count}")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
