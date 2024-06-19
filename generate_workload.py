import json
from tqdm import tqdm

schedule_config = {"functions": []}

with open("candidates_out_1_14.json", "r") as inf:
    fns = json.load(inf)
    
ONE_SECOND = 1_000_000_000
ONE_MINUTE = 60_000_000_000
SCALE = 10
# DURATION = 1440
DURATION = 5  # Fix to 5 minutes first

for fn_name in fns.keys():
    fn_sub_dict = {"name": fn_name}
    invocations = []  # Contain scheduled trigger in nanoseconds starting from origin
    origin = 0
    for i in range(DURATION):
        num_invocations = int(fns[fn_name][i]) * SCALE
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

with open("generated_schedule.json", "w") as fp:
    json.dump(schedule_config, fp, indent=4)
