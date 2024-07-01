from typing import List

import numpy as np
import pandas as pd
import json
import os

import tqdm


dataset_dir = "azuretracedataset"

# We do not use the memory percentiles cos its only tied to an app and not a function
file_tags = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14"]

# Match on hashowner and hashapp
functions = {}

# trace dset is in milliseconds
# but ours is in microseconds
# make ours micro->milli

class FunctionTraceObject:
    uid: str  # simply concat HashOwner,HashApp,HashFunction to form 'uid' (in quotes becos its not sufficient to be unique)
    mean: int
    # runtime percentiles (in milliseconds)
    p0: int
    p1: int
    p25: int
    p50: int
    p75: int
    p99: int
    p100: int
    # invocation timestamps in minutes per the day
    invocations: np.array

    def __init__(self, uid):
        self.uid = uid
        self.mean = -1
        self.p0 = -1
        self.p1 = -1
        self.p25 = -1
        self.p50 = -1
        self.p75 = -1
        self.p99 = -1
        self.p100 = -1
        self.invocations = None
        
    def is_valid(self) -> bool:
        """Returns true if all the fields are populated
        Just a precaution in case the uid shows up in just one file and not the other
        """
        return self.mean != -1 and \
            self.p0 != -1 and \
            self.p1 != -1 and \
            self.p25 != -1 and \
            self.p50 != -1 and \
            self.p75 != -1 and \
            self.p99 != -1 and \
            self.p100 != -1 and \
            self.invocations is not None

fn_dict = {}
num_invocations = 1440  # 1440 minutes in a day
invocation_columns = [str(i) for i in range(1, num_invocations+1)]

for file_tag in file_tags:
    func_dur_df = pd.read_csv(os.path.join(dataset_dir, f"function_durations_percentiles.anon.d{file_tag}.csv"))
    func_ivc_df = pd.read_csv(os.path.join(dataset_dir, f"invocations_per_function_md.anon.d{file_tag}.csv"))
    
    for index, row in tqdm.tqdm(func_dur_df.iterrows()):
        uid = row["HashOwner"] + row["HashApp"] + row["HashFunction"]
        if uid not in fn_dict:
            fn_dict[uid] = FunctionTraceObject(uid)
        # Ignore the exact same uid that has already been populated
        elif uid in fn_dict and fn_dict[uid].mean != -1:
            continue
            
        fto: FunctionTraceObject = fn_dict[uid]
        fto.mean = row["Average"]
        fto.p0 = row["percentile_Average_0"]
        fto.p1 = row["percentile_Average_1"]
        fto.p25 = row["percentile_Average_25"]
        fto.p50 = row["percentile_Average_50"]
        fto.p75 = row["percentile_Average_75"]
        fto.p99 = row["percentile_Average_99"]
        fto.p100 = row["percentile_Average_100"]
    for index, row in tqdm.tqdm(func_ivc_df.iterrows()):
        uid = row["HashOwner"] + row["HashApp"] + row["HashFunction"]
        if uid not in fn_dict:
            fn_dict[uid] = FunctionTraceObject(uid)
        elif uid in fn_dict and fn_dict[uid].invocations is not None:
            continue
        fto: FunctionTraceObject = fn_dict[uid]
        fto.invocations = row[invocation_columns].to_numpy(dtype=int)
    break

with open("results/statistics.json", "r") as fp:
    candidates_json = json.load(fp)
    candidates = {}
    # Convert all timings from microseconds to milliseconds
    for fn_name in candidates_json.keys():
        candidates[fn_name] = FunctionTraceObject("nonsense")
        candidates[fn_name].mean = candidates_json[fn_name]["runtime"]["mean"] / 1000
        candidates[fn_name].p0 = candidates_json[fn_name]["runtime"]["p0"] / 1000
        candidates[fn_name].p1 = candidates_json[fn_name]["runtime"]["p1"] / 1000
        candidates[fn_name].p25 = candidates_json[fn_name]["runtime"]["p25"] / 1000
        candidates[fn_name].p50 = candidates_json[fn_name]["runtime"]["p50"] / 1000
        candidates[fn_name].p75 = candidates_json[fn_name]["runtime"]["p75"] / 1000
        candidates[fn_name].p99 = candidates_json[fn_name]["runtime"]["p99"] / 1000
        candidates[fn_name].p100 = candidates_json[fn_name]["runtime"]["p100"] / 1000
    
def distance(fto1: FunctionTraceObject, fto2: FunctionTraceObject) -> int:
    d_mean = fto1.mean - fto2.mean
    d_p0 = fto1.p0 - fto2.p0
    d_p1 = fto1.p1 - fto2.p1
    d_p25 = fto1.p25 - fto2.p25
    d_p50 = fto1.p50 - fto2.p50
    d_p75 = fto1.p75 - fto2.p75
    d_p99 = fto1.p99 - fto2.p99
    d_p100 = fto1.p100 - fto2.p100
    return d_mean**2 + d_p0**2 + d_p1**2 + d_p25**2 + d_p50**2 + d_p75**2 + d_p99**2 + d_p100**2

best_worst = {"data": []}

# TODO: Check how close the euclidean distance for the best and worst candidate is
# TODO: Obtain the p99 for 10 random functions and plot their pdfs
def closest_candidate(candidates: dict, fto: FunctionTraceObject) -> str:
    worst_candidate = None
    worst_distance = None
    
    best_candidate = None
    best_distance = None
    for candidate in candidates.keys():
        d = distance(candidates[candidate], fto)
        if best_distance is None or d < best_distance:
            best_distance = d
            best_candidate = candidate
        
        if worst_distance is None or d > worst_distance:
            worst_distance = d
            worst_candidate = candidate
    best_worst["data"].append({
        "best_c": best_candidate,
        "best_d": best_distance,
        "worst_c": worst_candidate,
        "worst_d": worst_distance,
    })
            
    return best_candidate
    
best_candidate_counts = {fn_name: 0 for fn_name in candidates.keys()}
candidates_out = {fn_name: np.zeros((num_invocations,)) for fn_name in candidates.keys()}
for uid in fn_dict.keys():
    fto: FunctionTraceObject = fn_dict[uid]
    if not fto.is_valid():
        continue
    best_candidate = closest_candidate(candidates, fto)
    best_candidate_counts[best_candidate] += 1
    candidates_out[best_candidate] += fto.invocations

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

with open("candidates_out.json", "w") as outf:
    json.dump(candidates_out, outf, cls=NpEncoder)
with open("best_candidate_counts.json", "w") as outf:
    json.dump(best_candidate_counts, outf)
with open("best_worst.json", "w") as outf:
    json.dump(best_worst, outf)