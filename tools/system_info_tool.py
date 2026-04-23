"""
Mini-Ultra System Info Tool
Retrieve system information and health metrics.
"""
import os
import platform
import psutil
from datetime import datetime
from typing import Any, Dict
from tools.base import BaseTool


class SystemInfoTool(BaseTool):
    name = "system_info"
    description = "Get system information including CPU, memory, disk, and network stats"

    def execute(self, category: str = "all", **kwargs) -> Dict[str, Any]:
        try:
            if category == "cpu":
                return {"success": True, "result": self._cpu_info()}
            elif category == "memory":
                return {"success": True, "result": self._memory_info()}
            elif category == "disk":
                return {"success": True, "result": self._disk_info()}
            elif category == "network":
                return {"success": True, "result": self._network_info()}
            elif category == "platform":
                return {"success": True, "result": self._platform_info()}
            elif category == "all":
                return {
                    "success": True,
                    "result": {
                        "platform": self._platform_info(),
                        "cpu": self._cpu_info(),
                        "memory": self._memory_info(),
                        "disk": self._disk_info(),
                        "network": self._network_info(),
                        "timestamp": datetime.now().isoformat(),
                    }
                }
            else:
                return {"success": False, "error": f"Unknown category: {category}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _platform_info(self) -> dict:
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
        }

    def _cpu_info(self) -> dict:
        return {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "usage_percent": psutil.cpu_percent(interval=0.5),
            "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
        }

    def _memory_info(self) -> dict:
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "percent": mem.percent,
        }

    def _disk_info(self) -> dict:
        disk = psutil.disk_usage("/")
        return {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent,
        }

    def _network_info(self) -> dict:
        net = psutil.net_io_counters()
        return {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        }
