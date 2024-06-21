"""This script monitors the openwhisk activation poll output"""
import subprocess
import signal
import os
import time
import traceback


def sig_handler(signum, frame):
    process.kill()
    if start_time is None or end_time is None:
        # This happens if no activations were observed
        start_time = time.time()
        end_time = time.time()
    with open("experiment_aps.txt", "w") as outf:
        outf.write(f"Start           : {start_time}\n")
        outf.write(f"End             : {end_time}\n")
        outf.write(f"Duration        : {end_time-start_time} seconds\n")
        outf.write(f"Num activations : {num_activations}\n")
        outf.write(f"Invocations/sec : {num_activations/(end_time-start_time)}/s\n")    
    exit()


if __name__ == "__main__":
    command = ["wsk", "-i", "activation", "poll"]
    start_time = None
    end_time = None
    signal.signal(signal.SIGINT, sig_handler)
    print("Monitoring activation polls...")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    num_activations = 0
    try:
        while True:
            for line in process.stdout:
                if "Activation" in line:
                    # Shows non-blocking and blocking when actually fulfilled
                    num_activations += 1
                    if start_time is None:
                        start_time = time.time()
                    end_time = time.time()
            return_code = process.wait()
            time.sleep(1)
    except Exception as e:
        print(traceback.format_exc())