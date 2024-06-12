import json
import os

cwd = "/mnt/sdb/Jotham/serverless-benchmarks/results"
data = {}
expected_num_repetitions = 50

for file in os.listdir(cwd):
    if not file.endswith(".json"):
        continue
    with open(f"{cwd}/{file}", "r") as f:
        exp = json.load(f)
        exp_name = file.split(".")[0]
        data[exp_name] = {}
        
        memusage = 0  # KB
        runtime = 0  # microseconds
        
        subexp_name = list(exp['_invocations'].keys())[0]  # guaranteed only one
        num_repetitions = len(exp['_invocations'][subexp_name].keys())
        assert expected_num_repetitions == num_repetitions
        for activation_id in exp['_invocations'][subexp_name].keys():
            memusage += exp['_invocations'][subexp_name][activation_id]['output']['memusage']
            runtime += exp['_invocations'][subexp_name][activation_id]['output']['results_time']
        data[exp_name]['memusage'] = memusage / num_repetitions
        data[exp_name]['runtime'] = runtime / num_repetitions
        
with open("statistics.json", "w") as outf:
    json.dump(data, outf, indent=4)