"""
Measure memory consumption of all docker containers
"""

import subprocess
import time
import psutil

def get_memory_metrics(pid):
    try:
        process = psutil.Process(pid)
        with process.oneshot():
            memory_info = process.memory_full_info()
            uss = memory_info.uss  # Unique set size
            pss = memory_info.pss  # Proportional set size
        return uss, pss
    except psutil.NoSuchProcess:
        return None, None
        


def measure(container_name: str, measure_interval: int, measurement_file: str) -> None:
    # Get long form of container_id and report error if its down
    cmd = 'docker inspect --format="{{.Id}}" ' + container_name
    p = subprocess.run(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    if p.returncode != 0:
        print("Something went wrong ")
        return
    container_id = p.stdout.decode()
    
    # Get pid for container
    cmd = 'docker inspect -f "{{.State.Pid}}" ' + container_name
    p = subprocess.run(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    if p.returncode != 0:
        print("Something went wrong ")
        return
    pid = int(p.stdout.decode())
    uss, pss = get_memory_metrics(pid)
    if uss is not None and pss is not None:
        print(f"USS: {uss / 1024 / 1024:.2f} MB")
        print(f"PSS: {pss / 1024 / 1024:.2f} MB")
    
    # print(f"Container id = {container_id}")
    # f = open(measurement_file, "a")
    
    # while True:
    #     time_start = time.perf_counter_ns()
    #     longId = "docker-" + container_id + ".scope"
    

if __name__ == "__main__":
    measure("invoker0", 0, "")