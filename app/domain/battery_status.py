from enum import Enum


class BatteryStatus(str, Enum):
    AVAILABLE = "available"
    CHARGING = "charging"
    DISCHARGING = "discharging"
    OFFLINE = "offline"