import json
# qemu has experiments postfixed
qemu_results = "qemu-results/statistics.json"
host_results = "host-results/statistics.json"

with open(qemu_results, "r") as f:
    qemu = json.load(f)
    
with open(host_results, "r") as f:
    host = json.load(f)
    
def get_overhead(v1, v2):
    # Assume v1 is host, v2 is qemu
    return (v2 / v1) * 100
    # return ((v2 - v1) / v1) * 100.0
    # return ((v2 - v1) / v1) * 100.0
    
# Skip compression cos too much space requirements
benchmarks = [
    "110.dynamic-html",
    "120.uploader",
    "210.thumbnailer",
    "220.video-processing",
    "411.image-recognition",
    "501.graph-pagerank",
    "502.graph-mst",
    "503.graph-bfs",
]

for benchmark in benchmarks:
    print("*" * 25)
    print(f"{benchmark}")
    host_df = host[benchmark + "_experiments"]
    qemu_df = qemu[benchmark + "_experiments"]
    # memusage
    host_mem_p0 = host_df["memusage"]["p0"]
    host_mem_p1 = host_df["memusage"]["p1"]
    host_mem_p25 = host_df["memusage"]["p25"]
    host_mem_p50 = host_df["memusage"]["p50"]
    host_mem_p75 = host_df["memusage"]["p75"]
    host_mem_p99 = host_df["memusage"]["p99"]
    host_mem_p100 = host_df["memusage"]["p100"]
    
    qemu_mem_p0 = qemu_df["memusage"]["p0"]
    qemu_mem_p1 = qemu_df["memusage"]["p1"]
    qemu_mem_p25 = qemu_df["memusage"]["p25"]
    qemu_mem_p50 = qemu_df["memusage"]["p50"]
    qemu_mem_p75 = qemu_df["memusage"]["p75"]
    qemu_mem_p99 = qemu_df["memusage"]["p99"]
    qemu_mem_p100 = qemu_df["memusage"]["p100"]
    
    print("p0 memusage overhead   " + str(get_overhead(host_mem_p0, qemu_mem_p0)))
    print("p1 memusage overhead   " + str(get_overhead(host_mem_p1, qemu_mem_p1)))
    print("p25 memusage overhead  " + str(get_overhead(host_mem_p25, qemu_mem_p25)))
    print("p50 memusage overhead  " + str(get_overhead(host_mem_p50, qemu_mem_p50)))
    print("p75 memusage overhead  " + str(get_overhead(host_mem_p75, qemu_mem_p75)))
    print("p99 memusage overhead  " + str(get_overhead(host_mem_p99, qemu_mem_p99)))
    print("p100 memusage overhead " + str(get_overhead(host_mem_p100, qemu_mem_p100)))
    
    # runtime
    
    host_runtime_p0 = host_df["runtime"]["p0"]
    host_runtime_p1 = host_df["runtime"]["p1"]
    host_runtime_p25 = host_df["runtime"]["p25"]
    host_runtime_p50 = host_df["runtime"]["p50"]
    host_runtime_p75 = host_df["runtime"]["p75"]
    host_runtime_p99 = host_df["runtime"]["p99"]
    host_runtime_p100 = host_df["runtime"]["p100"]
    
    qemu_runtime_p0 = qemu_df["runtime"]["p0"]
    qemu_runtime_p1 = qemu_df["runtime"]["p1"]
    qemu_runtime_p25 = qemu_df["runtime"]["p25"]
    qemu_runtime_p50 = qemu_df["runtime"]["p50"]
    qemu_runtime_p75 = qemu_df["runtime"]["p75"]
    qemu_runtime_p99 = qemu_df["runtime"]["p99"]
    qemu_runtime_p100 = qemu_df["runtime"]["p100"]
    
    print("p0 runtime overhead   " + str(get_overhead(host_runtime_p0, qemu_runtime_p0)))
    print("p1 runtime overhead   " + str(get_overhead(host_runtime_p1, qemu_runtime_p1)))
    print("p25 runtime overhead  " + str(get_overhead(host_runtime_p25, qemu_runtime_p25)))
    print("p50 runtime overhead  " + str(get_overhead(host_runtime_p50, qemu_runtime_p50)))
    print("p75 runtime overhead  " + str(get_overhead(host_runtime_p75, qemu_runtime_p75)))
    print("p99 runtime overhead  " + str(get_overhead(host_runtime_p99, qemu_runtime_p99)))
    print("p100 runtime overhead " + str(get_overhead(host_runtime_p100, qemu_runtime_p100)))
    
    print("*" * 25)
    
