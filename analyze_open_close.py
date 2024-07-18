import json
import os
import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--name", type=str)
options = parser.parse_args()

DIR_PATH = f"./open_close_{options.name}"
PREFIX = "experiments_open_close_"
ACTION = "python-3.7"

def get_benchmark_name(filename: str) -> str:
    return filename.replace(PREFIX, "").replace(".json", "") + "-" + ACTION

if not os.path.exists(DIR_PATH) or not os.path.isdir(DIR_PATH):
    print("No results folder")
    exit(1)
    
def __convert_str_to_timestamp(ts: str):
    seconds, microseconds = ts.split(".")
    seconds = int(seconds)
    microseconds = int(float('0.' + microseconds) * 1e6)
    dt = datetime.datetime.fromtimestamp(seconds)
    dt = dt + datetime.timedelta(microseconds=microseconds)
    return dt
    
# Used to keep track of schedule duration
earliest_invocation_ts = None
latest_invocation_ts = None

for dirpath, dirnames, filenames in os.walk(DIR_PATH):
    for filename in filenames:
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(DIR_PATH, filename), "r") as fp:
            result = json.load(fp)
        benchmark = get_benchmark_name(filename)
        if benchmark not in result["_invocations"]:
            print(f"Skipping {benchmark}")
            continue
        for _, invocation in result["_invocations"][benchmark].items():
            if "begin" not in invocation["output"]:
                # Skip failure
                continue
            begin_ts = __convert_str_to_timestamp(invocation["output"]["begin"])
            end_ts = __convert_str_to_timestamp(invocation["output"]["end"])
            if earliest_invocation_ts is None or begin_ts < earliest_invocation_ts:
                earliest_invocation_ts = begin_ts
            if latest_invocation_ts is None or end_ts > latest_invocation_ts:
                latest_invocation_ts = end_ts

# Just interested in total schedule at the moment
print(f"Earliest invocation = {earliest_invocation_ts}")
print(f"Latest invocation   = {latest_invocation_ts}")
invocation_duration = int((latest_invocation_ts - earliest_invocation_ts) / datetime.timedelta(seconds=1))
print(f"Total invocation duration = {invocation_duration} seconds")

with open(f"{options.name}_open_close.txt", "w") as outf:
    outf.write(f"Earliest invocation = {earliest_invocation_ts}")
    outf.write(f"Latest invocation   = {latest_invocation_ts}")
    outf.write(f"Total invocation duration = {invocation_duration} seconds")
