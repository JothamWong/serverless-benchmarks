# Schedule

SeBS supports open and open-closed (partially open) workload generation in addition to the closed loop workload wherein a single benchmark is invoked continuously. In open and open-closed workloads, a schedule is provided which contains a list of serverless functions and the timings to invoke them.

## Creating the schedule file

The benchmark suite currently reproduces the high level methodology used by CodeCrunch (ASPLOS'24) and FaasCache (ASPLOS'21).

Either run `./azuretracedataset/get.sh` to download the Microsoft Azure Trace dataset or obtain the trace from some other sources.

Next, for each serverless function you want to include in the workload, benchmark the function in a closed-loop for 1000 invocations (up to you) using `run_all.sh`. You can modify the script to add or remove benchmarks as you want. After all the functions have been benchmarked, run `python3 results/get_stats.py` to create the `statistics.json` file which contain the runtime and memory percentiles for each serverless function.

Then run `python3 generate_candidates.py` to generate the candidates. The candidates is a mapping of each function in the azure trace to a corresponding serverless function in your benchmark suite based on the Euclidean distance between the trace's runtime percentiles and the benchmark function's runtime percentile. One may modify the script to include the memory percentiles as well, but I personally din add them as I found that it added no differentiation.

With the `candidates_out.json` file, we are now ready to generate the schedule file `generated_schedule.json` using the command `python3 generate_workload.py --scale 0.001 --duration 1`. The default scale is 0.001 which simply scales up or down the number of invocations within the duration and the default duration is 1 minute.

## Running the schedule file

At this point, one may either invoke the schedule with a open or open-close workload.
In open workload, the requests in the schedule are invoked one after one, independent of whether the previous request has been satisfied or not. 

In the open-close workload, n client threads are spawned and the schedule is sharded into n sub-schedules for each client thread. The client thread then invokes its sub-schedule in a closed-loop manner.

Depending on the metrics/hypothesis one wishes to study, either workload might be appropriate.

### Open

```sh
python3 sebs.py schedule run-schedule --config config/openwhisk.json --deployment openwhisk --verbose --schedule_config generated_schedule.json --output-dir tmpscheduled --result_dir ha-results
```

### Open-close

```sh
python3 sebs.py open-close open-close --config config/openwhisk.json --deployment openwhisk --verbose --schedule_config generated_schedule.json --n_workers 5 --output-dir tmpscheduled --result_dir open_close
```

## Notes

Do not use `high-availability` mode for OpenWhisk. Many failures will occur.
Failures can occur when a serverless function invocation waits too long (queueing latency + processing latency exceeds function timeout).