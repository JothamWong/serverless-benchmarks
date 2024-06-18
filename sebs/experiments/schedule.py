from typing import Dict, List

import heapq

class ScheduleObject:
    def __init__(self, timestamp: int, fn_name: str):
        self.timestamp = timestamp
        self.fn_name = fn_name
    
    def __lt__(self, other: "ScheduleObject"):
        return self.timestamp < other.timestamp
        

class ScheduleConfig:
    """Helper class to deserialize from json file to configuration 
    file for scheduling experiment."""
    def __init__(self):
        self.fns = []  # List of fns to use for preparation
        self.schedule: List[ScheduleObject] = []
        
    @staticmethod
    def deserialize(config: dict) -> "ScheduleConfig":
        cfg = ScheduleConfig()
        for fn_dict in config["functions"]:
            fn_name = fn_dict["name"]
            cfg.fns.append(fn_name)
            invocations = fn_dict["invocations"]
            for ts in invocations:
                so = ScheduleObject(ts, fn_name)
                heapq.heappush(cfg.schedule, so)
        return cfg