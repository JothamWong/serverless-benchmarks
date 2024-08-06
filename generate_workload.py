import argparse
import sys
import json

args = argparse.ArgumentParser()
args.add_argument("--scale", type=float, default=0.001, help="Scaling the workload")
args.add_argument("--duration", type=int, default=1, help="How many minutes to run the workload for")
opts = args.parse_args()

schedule_config = {"functions": []}

with open("candidates_out_1_14.json", "r") as inf:
    fns = json.load(inf)
    
ONE_SECOND = 1_000_000_000
FIFTEEN_SECONDS = ONE_SECOND * 15
ONE_MINUTE = 60_000_000_000

SCALE = opts.scale
DURATION = opts.duration

fn_statistics = {}

for fn_name in fns.keys():
    fn_sub_dict = {"name": fn_name}
    invocations = []  # Contain scheduled trigger in nanoseconds starting from origin
    origin = 0
    for i in range(DURATION):
        num_invocations = int(fns[fn_name][i] * SCALE)
        # Uniformly distribute over the minute
        if num_invocations == 0:
            continue
        interval = int(ONE_MINUTE / num_invocations)
        for inv in range(num_invocations):
            timestamp = origin + interval * inv
            invocations.append(timestamp)
        origin += ONE_MINUTE
    fn_sub_dict["invocations"] = invocations
    schedule_config["functions"].append(fn_sub_dict)
    
    fn_statistics[fn_name] = len(invocations)

with open("generated_schedule.json", "w") as fp:
    json.dump(schedule_config, fp, indent=4)

# Print some statistics
statistics = f"Generated workload: scale={SCALE}, duration={DURATION}minutes"
max_width = max(len(fn_name) for fn_name in fn_statistics.keys()) + 1
total_invocations = 0
print("---------------------------------------------------------------")
print(statistics)
print("---------------------------------------------------------------")
for fn_name in fn_statistics.keys():
    print(f"{fn_name.ljust(max_width)}: {fn_statistics[fn_name]} invocations in {DURATION} minutes")
    total_invocations += fn_statistics[fn_name]
print("---------------------------------------------------------------")
print(f"Total invocations within {DURATION} min = {total_invocations}")
print(f"Theoretical rps = {total_invocations / (DURATION * 60)} requests/sec")
print("---------------------------------------------------------------")