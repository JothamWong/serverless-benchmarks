import json
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

cwd = "/mnt/sdb/home/Jotham/serverless-benchmarks/qemu-results"
data = {}
expected_num_repetitions = 1000


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super(NumpyEncoder, self).default(obj)


def plot_cdf(exp_name: str, metric: str, data: np.array):
    p99 = np.percentile(data, 99)
    fig, ax = plt.subplots(figsize=(10,5))
    ax.axvline(p99, color='r', linestyle='--', label='p99')
    ax.annotate(f'p99:{p99:.0f}', xy=(p99, 0.9), xytext=(p99 + 5000, 0.85), 
                arrowprops=dict(facecolor='black', arrowstyle='->'),fontsize=12)
    sns.ecdfplot(data=data)
    fig.savefig(f"{exp_name}_{metric}_percentile.png")
    plt.close()
    
def plot_pdf(exp_name: str, metric: str, data: np.array):
    plt.figure(figsize=(10,5))
    sns.kdeplot(data=data)
    plt.savefig(f"{exp_name}_{metric}_pdf.png")
    plt.close()

# Remove statistics.json if it exists
statistics_path = f"{cwd}/statistics.json"
if os.path.exists(statistics_path):
    os.remove(statistics_path)

for file in os.listdir(cwd):
    if not file.endswith(".json"):
        continue
    with open(f"{cwd}/{file}", "r") as f:
        print(f"Handling {file}")
        exp = json.load(f)
        exp_name = ".".join(file.split(".")[0:2])
        data[exp_name] = {}
        data[exp_name]['memusage'] = {}
        data[exp_name]['runtime'] = {}
        subexp_name = list(exp['_invocations'].keys())[0]  # guaranteed only one
        num_repetitions = len(exp['_invocations'][subexp_name].keys())
        latencies = []
        memusages = []
        assert expected_num_repetitions == num_repetitions
        for activation_id in exp['_invocations'][subexp_name].keys():
            memusages.append(exp['_invocations'][subexp_name][activation_id]['output']['memusage'])
            latencies.append(exp['_invocations'][subexp_name][activation_id]['output']['results_time'])
        latencies = np.asarray(latencies)
        memusages = np.asarray(memusages)
        plot_cdf(exp_name, "latencies", latencies)
        plot_pdf(exp_name, "latencies", latencies)
        plot_cdf(exp_name, "memusage", memusages)
        plot_pdf(exp_name, "memusage", memusages)
        
        data[exp_name]['memusage']['mean'] = np.average(memusages)
        data[exp_name]['memusage']['p0'] = np.min(memusages)
        data[exp_name]['memusage']['p1'] = np.percentile(memusages, 1)
        data[exp_name]['memusage']['p25'] = np.percentile(memusages, 25)
        data[exp_name]['memusage']['p50'] = np.percentile(memusages, 50)
        data[exp_name]['memusage']['p75'] = np.percentile(memusages, 75)
        data[exp_name]['memusage']['p99'] = np.percentile(memusages, 99)
        data[exp_name]['memusage']['p100'] = np.max(memusages)
        
        data[exp_name]['runtime']['mean'] = np.average(latencies)
        data[exp_name]['runtime']['p0'] = np.min(latencies)
        data[exp_name]['runtime']['p1'] = np.percentile(latencies, 1)
        data[exp_name]['runtime']['p25'] = np.percentile(latencies, 25)
        data[exp_name]['runtime']['p50'] = np.percentile(latencies, 50)
        data[exp_name]['runtime']['p75'] = np.percentile(latencies, 75)
        data[exp_name]['runtime']['p99'] = np.percentile(latencies, 99)
        data[exp_name]['runtime']['p100'] = np.max(latencies)
        
with open("statistics.json", "w") as outf:
    json.dump(data, outf, indent=4, cls=NumpyEncoder)