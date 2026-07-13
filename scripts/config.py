"""Radio configuration for the swarm. Edit these to match your setup."""

# One URI per flying drone. The last byte of the address is the drone's P2P id,
# so E7E7E7E701 becomes id 1. Keep ids in the range 1..9.
DRONE_URIS = [
    "radio://0/80/2M/E7E7E7E701",
    "radio://0/80/2M/E7E7E7E702",
    "radio://0/80/2M/E7E7E7E703",
    "radio://0/80/2M/E7E7E7E704",
    "radio://0/80/2M/E7E7E7E705",
    "radio://0/80/2M/E7E7E7E706",
]

# The sniffer is a spare Crazyflie running the sniffer app, connected over USB.
SNIFFER_URI = "usb://0"

# A drone below this voltage will not take off (CHARGED_FOR_TAKEOFF_VOLTAGE in settings.h).
TAKEOFF_VOLTAGE = 4.0

# Circle radius / line spacing, in metres. Must fit inside the flight box.
FORMATION_RADIUS = 0.45


def drone_id(uri):
    return int(uri[-2:], 16)
