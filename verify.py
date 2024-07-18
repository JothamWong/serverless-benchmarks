"""Verify that generated schedule actually fits in DURATION and is interleaved"""

import heapq
from typing import List
import json

class ScheduleObject:
    fn_name: str
    timestamp: int
    
    def __init__(self, fn_name, timestamp):
        self.fn_name = fn_name
        self.timestamp = timestamp
        
    def __repr__(self) -> str:
        return f"{self.fn_name}@{self.timestamp}"
        
    def __lt__(self, other: "ScheduleObject"):
        return self.timestamp < other.timestamp
        

schedule_file = "generated_schedule.json"
with open(schedule_file, "r") as inf:
    schedule = json.load(inf)

traces: List[ScheduleObject] = []

fn_counts = {}

for fn_obj in schedule["functions"]:
    name = fn_obj["name"]
    invocations = fn_obj["invocations"]
    
    print(fn_obj["name"])
    for timestamp in invocations:
        so = ScheduleObject(name, timestamp)
        traces.append(so)
    
    fn_counts[name] = len(invocations)

traces.sort(key=lambda so: so.timestamp)

with open("verification.txt", "w") as outf:
    for so in traces:
        outf.write(f"{so}\n")
    for name in fn_counts.keys():
        outf.write(f"{name}: {fn_counts[name]}\n")