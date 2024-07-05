import json
import numpy as np
from datetime import datetime, timedelta
import argparse
import random
from collections import defaultdict

ONE_SECOND = 1_000_000_000

parser = argparse.ArgumentParser("Generate Inter-arrival-times (IATs) schedule")
parser.add_argument("-l", "--lambda_rate", default=4, type=int, help="Lambda rate for poisson per minute")
parser.add_argument("-d", "--duration", default=1, type=int, help="Duration of schedule in minutes")
parser.add_argument("-e", "--events", default="events.json", help="JSON file containing candidate serverless functions and their corresponding probabilities")
parser.add_argument("-o", "--output_file", default="schedule.json", help="Output destination")
parser.add_argument("-s", "--seed", default=42, type=int, help="Random seed")
options = parser.parse_args()

random.seed(options.seed)

with open(options.events, "r") as inf:
    events = json.load(inf)

# Do a fact check that the probabilities sum up to 100 and none are negative
total_prob = 0
for event, prob in events.items():
    if prob < 0:
        raise ValueError(f"Illegal probability assigned to {event}")
    total_prob += prob
if total_prob != 100:
    raise ValueError(f"Illegal probability distribution for {options.events}!")


def sample_candidate():
    candidates = list(events.keys())
    probabilities = list(events.values())
    return random.choices(candidates, weights=probabilities, k=1)[0]


def generate_poisson_workload(lambda_rate, duration_minutes, out_file: str):
    """
    :param lambda_rate: average number of requests per minute
    :param duration_minutes: total duration of workload in minutes
    :param out_file: destination to write schedule to
    """
    start_time = datetime.fromtimestamp(0)
    inter_arrival_times = np.random.exponential(1 / lambda_rate, size=lambda_rate*duration_minutes)
    
    current_time = start_time
    
    raw_counts = defaultdict(int)
    schedule_config = {"functions": []}
    fn_dicts = {}
        
    for interval in inter_arrival_times:
        current_time += timedelta(minutes=interval)
        event = sample_candidate()
        
        if event not in fn_dicts:
            fn_sub_dict = {"name": event, "invocations": []}
            fn_dicts[event] = fn_sub_dict
        
        fn_dicts[event]["invocations"].append(current_time.timestamp() * ONE_SECOND)
        raw_counts[event] += 1
    
    for fn_sub_dict in fn_dicts.values():
        schedule_config["functions"].append(fn_sub_dict)
    
    with open(out_file, "w") as outf:
        json.dump(schedule_config, outf, indent=4)
            
    max_width = max(len(fn_name) for fn_name in raw_counts.keys()) + 1
    print("*" * 20)
    print("Workload Statistics")
    print(f"Lambda rate : {options.lambda_rate}")
    print(f"Duration    : {options.duration}")
    print("*" * 20)
    for event, count in raw_counts.items():
        print(f"{event.ljust(max_width)}: {count} times")
    print("*" * 20)
    

generate_poisson_workload(options.lambda_rate, options.duration, options.output_file)