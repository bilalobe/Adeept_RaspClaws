#!/usr/bin/python3
# File name   : Ultrasonic.py
# Description : Detection distance and tracking with ultrasonic
# Website     : www.gewbot.com
# Author      : William
# Date        : 2019/08/28
import os
import psutil
import json
import logging
import time
from dataclasses import asdict, dataclass
from typing import Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class SystemStatus:
    cpu_temp: float = 0.0
    cpu_usage: float = 0.0
    ram_usage: float = 0.0
    stability: float = 0.0
    uptime: float = 0.0

class SystemMonitor:
    def __init__(self):
        self.start_time = time.time()

    def get_cpu_temp(self) -> float:
        """Get CPU temperature"""
        try:
            if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
                with open('/sys/class/thermal/thermal_zone0/temp') as f:
                    temp = float(f.read()) / 1000.0
                return round(temp, 1)
        except Exception as e:
            logger.warning(f"Failed to read CPU temperature: {e}")
        return 0.0

    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        return psutil.cpu_percent()

    def get_ram_usage(self) -> float:
        """Get RAM usage percentage"""
        return psutil.virtual_memory().percent

    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - self.start_time

    def get_status(self) -> SystemStatus:
        """Get complete system status"""
        from move import calc_stability_metric
        
        return SystemStatus(
            cpu_temp=self.get_cpu_temp(),
            cpu_usage=self.get_cpu_usage(),
            ram_usage=self.get_ram_usage(),
            stability=calc_stability_metric(),
            uptime=self.get_uptime()
        )

    def to_json(self) -> str:
        """Get system status as JSON string"""
        return json.dumps(asdict(self.get_status()))

# Global monitor instance
monitor = SystemMonitor()
