import json
import logging
import functools
import os
import traceback
from typing import cast, Optional, List
from datetime import datetime, timedelta
import time
import subprocess
import sys
import signal
import shutil
import matplotlib.pyplot as plt

from multiprocessing import Process, Queue
from dataclasses import dataclass
from tqdm import tqdm
import numpy as np

from multiprocessing.pool import ThreadPool

import click

import sebs
from sebs import SeBS
import sebs.experiments
from sebs.experiments.schedule import ScheduleObject, ScheduleConfig
from sebs.types import Storage as StorageTypes
from sebs.regression import regression_suite
from sebs.utils import update_nested_dict, catch_interrupt
from sebs.faas import System as FaaSSystem
from sebs.faas.function import Trigger
import sebs.utils


PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))

deployment_client: Optional[FaaSSystem] = None
sebs_client: Optional[SeBS] = None


class ExceptionProcesser(click.Group):
    def __call__(self, *args, **kwargs):
        try:
            return self.main(*args, **kwargs)
        except Exception as e:
            logging.error(e)
            traceback.print_exc()
            logging.info("# Experiments failed! See out.log for details")
        finally:
            # Close
            if deployment_client is not None:
                deployment_client.shutdown()
            if sebs_client is not None:
                sebs_client.shutdown()


def simplified_common_params(func):
    @click.option(
        "--config",
        required=True,
        type=click.Path(readable=True),
        help="Location of experiment config.",
    )
    @click.option("--output-dir", default=os.path.curdir, help="Output directory for results.")
    @click.option("--output-file", default="out.log", help="Output filename for logging.")
    @click.option(
        "--cache",
        default=os.path.join(os.path.curdir, "cache"),
        help="Location of experiments cache.",
    )
    @click.option("--verbose/--no-verbose", default=False, help="Verbose output.")
    @click.option(
        "--preserve-out/--no-preserve-out",
        default=True,
        help="Preserve current results in output directory.",
    )
    @click.option(
        "--language",
        default=None,
        type=click.Choice(["python", "nodejs"]),
        help="Benchmark language",
    )
    @click.option("--language-version", default=None, type=str, help="Benchmark language version")
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def common_params(func):
    @click.option(
        "--update-code/--no-update-code",
        default=False,
        help="Update function code in cache and cloud deployment.",
    )
    @click.option(
        "--update-storage/--no-update-storage",
        default=False,
        help="Update benchmark storage files in cloud deployment.",
    )
    @click.option(
        "--deployment",
        default=None,
        type=click.Choice(["azure", "aws", "gcp", "local", "openwhisk"]),
        help="Cloud deployment to use.",
    )
    @click.option(
        "--resource-prefix",
        default=None,
        type=str,
        help="Resource prefix to look for.",
    )
    @simplified_common_params
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def parse_common_params(
    config,
    output_dir,
    output_file,
    cache,
    verbose,
    preserve_out,
    update_code,
    update_storage,
    deployment,
    language,
    language_version,
    resource_prefix: Optional[str] = None,
    initialize_deployment: bool = True,
    ignore_cache: bool = False,
    storage_configuration: Optional[str] = None
):

    global sebs_client, deployment_client
    config_obj = json.load(open(config, "r"))
    os.makedirs(output_dir, exist_ok=True)
    logging_filename = os.path.abspath(os.path.join(output_dir, output_file))

    sebs_client = sebs.SeBS(cache, output_dir, verbose, logging_filename)
    output_dir = sebs.utils.create_output(output_dir, preserve_out, verbose)
    
    sebs_client.logging.info("Created experiment output at {}".format(output_dir))

    # CLI overrides JSON options
    update_nested_dict(config_obj, ["experiments", "runtime", "language"], language)
    update_nested_dict(config_obj, ["experiments", "runtime", "version"], language_version)
    update_nested_dict(config_obj, ["deployment", "name"], deployment)
    update_nested_dict(config_obj, ["experiments", "update_code"], update_code)
    update_nested_dict(config_obj, ["experiments", "update_storage"], update_storage)

    if storage_configuration:
        cfg = json.load(open(storage_configuration, 'r'))
        update_nested_dict(config_obj, ["deployment", deployment, "storage"], cfg)

    if initialize_deployment:
        deployment_client = sebs_client.get_deployment(
            config_obj["deployment"], logging_filename=logging_filename
        )
        deployment_client.initialize(resource_prefix=resource_prefix)
    else:
        deployment_client = None

    if ignore_cache:
        sebs_client.ignore_cache()

    catch_interrupt()

    return config_obj, output_dir, logging_filename, sebs_client, deployment_client


@click.group(cls=ExceptionProcesser)
def cli():
    pass


@cli.group()
def benchmark():
    pass


@benchmark.command()
@click.argument("benchmark", type=str)  # , help="Benchmark to be used.")
@click.argument(
    "benchmark-input-size", type=click.Choice(["test", "small", "large"])
)  # help="Input test size")
@click.option("--repetitions", default=5, type=int, help="Number of experimental repetitions.")
@click.option(
    "--trigger",
    type=click.Choice(["library", "http"]),
    default="http",
    help="Function trigger to be used.",
)
@click.option(
    "--memory",
    default=None,
    type=int,
    help="Override default memory settings for the benchmark function.",
)
@click.option(
    "--timeout",
    default=None,
    type=int,
    help="Override default timeout settings for the benchmark function.",
)
@click.option(
    "--function-name",
    default=None,
    type=str,
    help="Override function name for random generation.",
)
@click.option(
    "--image-tag-prefix",
    default=None,
    type=str,
    help="Attach prefix to generated Docker image tag.",
)
@common_params
def invoke(
    benchmark,
    benchmark_input_size,
    repetitions,
    trigger,
    memory,
    timeout,
    function_name,
    image_tag_prefix,
    **kwargs,
):

    (
        config,
        output_dir,
        logging_filename,
        sebs_client,
        deployment_client,
    ) = parse_common_params(**kwargs)
    if image_tag_prefix is not None:
        sebs_client.config.image_tag_prefix = image_tag_prefix

    experiment_config = sebs_client.get_experiment_config(config["experiments"])
    update_nested_dict(config, ["experiments", "benchmark"], benchmark)
    benchmark_obj = sebs_client.get_benchmark(
        benchmark,
        deployment_client,
        experiment_config,
        logging_filename=logging_filename,
    )
    if memory is not None:
        benchmark_obj.benchmark_config.memory = memory
    if timeout is not None:
        benchmark_obj.benchmark_config.timeout = timeout

    func = deployment_client.get_function(
        benchmark_obj,
        function_name if function_name else deployment_client.default_function_name(benchmark_obj),
    )
    storage = deployment_client.get_storage(replace_existing=experiment_config.update_storage)
    input_config = benchmark_obj.prepare_input(storage=storage, size=benchmark_input_size)

    result = sebs.experiments.ExperimentResult(experiment_config, deployment_client.config)
    result.begin()

    trigger_type = Trigger.TriggerType.get(trigger)
    triggers = func.triggers(trigger_type)
    if len(triggers) == 0:
        trigger = deployment_client.create_trigger(func, trigger_type)
    else:
        trigger = triggers[0]
    for i in range(repetitions):
        sebs_client.logging.info(f"Beginning repetition {i+1}/{repetitions}")
        print(f"{input_config=}")
        ret = trigger.sync_invoke(input_config)
        if ret.stats.failure:
            sebs_client.logging.info(f"Failure on repetition {i+1}/{repetitions}")
            # deployment_client.get_invocation_error(
            #    function_name=func.name, start_time=start_time, end_time=end_time
            # )
        result.add_invocation(func, ret)
    result.end()

    result_file = os.path.join(output_dir, f"{benchmark}_experiments.json")
    with open(result_file, "w") as out_f:
        out_f.write(sebs.utils.serialize(result))
    sebs_client.logging.info("Save results to {}".format(os.path.abspath(result_file)))
    
"""
Schedule invocations with a json file of the format:
{
  "functions": [
    {
      "name": "benchmark-name",
      "invocations": [
        {
          "timestamp": "2024-06-18T10:30:00Z"
        },
        {
          "timestamp": "2024-06-18T14:00:00Z"
        }
      ]
    },
}
"""
@cli.group()
def schedule():
    pass

"""
Schedule is an open-loop benchmarking. Many failures due to system overload.
Force usage of library. Exposing action as http prevents simple non-blocking usage
"""
@schedule.command()
@click.option("--schedule_config", type=str, default="schedule.json", help="path to schedule")
@click.option(
    "--trigger_t",
    type=click.Choice(["library"]),
    default="library",
    help="Function trigger to be used.",
)
@click.option(
    "--memory",
    default=None,
    type=int,
    help="Override default memory settings for the benchmark function.",
)
@click.option(
    "--timeout",
    default=None,
    type=int,
    help="Override default timeout settings for the benchmark function.",
)
@click.option(
    "--result_dir",
    default="schedule-results",
    type=str,
    help="Results directory"
)
@common_params
def run_schedule(
    schedule_config,
    trigger_t,
    memory,
    timeout,
    result_dir,
    **kwargs,
):
    (
        config,
        output_dir,
        logging_filename,
        sebs_client,
        deployment_client,
    ) = parse_common_params(**kwargs)
    
    experiment_config = sebs_client.get_experiment_config(config["experiments"])
    with open(schedule_config, "r") as fp:
        schedule_config = json.load(fp)
    schedule_config = sebs_client.get_schedule_config(schedule_config)

    if os.path.exists(result_dir):
        shutil.rmtree(result_dir)
    os.mkdir(result_dir)

    # Loop and set up each benchmark trigger
    triggers_m = {}
    for benchmark in schedule_config.fns:
        update_nested_dict(config, ["experiments", "benchmark"], benchmark)
        benchmark_obj = sebs_client.get_benchmark(
            benchmark,
            deployment_client,
            experiment_config,
            logging_filename=logging_filename
        )
        # TODO: Make this better
        if memory is not None:
            benchmark_obj.benchmark_config.memory = memory
        if timeout is not None:
            benchmark_obj.benchmark_config.timeout = timeout

        func = deployment_client.get_function(
            benchmark_obj,
            deployment_client.default_function_name(benchmark_obj),
        )
        storage = deployment_client.get_storage(replace_existing=experiment_config.update_storage)
        # TODO: Make this individual
        input_config = benchmark_obj.prepare_input(storage=storage, size="small")
        
        result = sebs.experiments.ExperimentResult(experiment_config, deployment_client.config)
        result.begin()
        
        trigger_type = Trigger.TriggerType.get(trigger_t)
        triggers = func.triggers(trigger_type)
        if len(triggers) == 0:
            trigger = deployment_client.create_trigger(func, trigger_type)
        else:
            trigger = triggers[0]
        print(f"{benchmark=}")
        triggers_m[benchmark] = {}
        triggers_m[benchmark]["trigger"] = trigger
        triggers_m[benchmark]["function"] = func
        triggers_m[benchmark]["input"] = input_config
        triggers_m[benchmark]["result"] = result
        triggers_m[benchmark]["activation_ids"] = []
        triggers_m[benchmark]["success"] = 0
        triggers_m[benchmark]["failure"] = 0
    
    # Scheduling main loop
    invocation_start = time.time_ns()
    for so in schedule_config.schedule:
        now = time.time_ns()
        scheduled_time = invocation_start + so.timestamp  # in nanoseconds
        if scheduled_time > now:
            delta_s = (scheduled_time - now) / 1_000_000_000
            # sebs_client.logging.info(f"Sleeping for {delta_s} seconds")
            time.sleep(delta_s)

        sebs_client.logging.info(f"Invoking {so.fn_name} at {scheduled_time}")
        trigger = triggers_m[so.fn_name]["trigger"] 
        input_config = triggers_m[so.fn_name]["input"]
        aids = triggers_m[so.fn_name]["activation_ids"]
        
        ret = trigger.openwhisk_nonblocking_invoke(input_config)
        # Store request time here
        if "request_time" not in triggers_m[so.fn_name].keys():
            triggers_m[so.fn_name]["request_time"] = {}
        if not ret.failure:
            triggers_m[so.fn_name]["request_time"][ret.request_id] = scheduled_time
        aids.append(ret)
    # End of actual invocation duration, most likely will not be DURATION
    invocation_end = time.time_ns()

    time.sleep(2)
    # Collect results main loop, can now block until result is done
    # becos metrics are saved locally at the node itself
    
    # Keep track of failures
    failures = {}
    collection_start = time.time_ns()
    for benchmark in triggers_m.keys():
        trigger = triggers_m[benchmark]["trigger"]
        func = triggers_m[benchmark]["function"]
        result = triggers_m[benchmark]["result"]
        for aid in triggers_m[benchmark]["activation_ids"]:
            if aid.request_id == "":
                # Means that invocation attempt itself wasnt even successful
                triggers_m[benchmark]["failure"] += 1
                continue
            
            ret = trigger.parse_nb_results(aid)
            if ret.stats.failure:
                triggers_m[benchmark]["failure"] += 1
                failures[ret.request_id] = ret.failureReason
            else:
                triggers_m[benchmark]["success"] += 1
            result.add_invocation(func, ret.executionResult)
        result.end()
        # Save separately
        result_file = os.path.join(result_dir, f"experiments_scheduled_{benchmark}.json")
        with open(result_file, "w") as out_f:
            out_f.write(sebs.utils.serialize(result))
        sebs_client.logging.info("Save results to {}".format(os.path.abspath(result_file)))

    collection_end = time.time_ns()
    
    with open(os.path.join(result_dir, "experiments_scheduled_failure.json"), "w") as outf:
        json.dump(failures, outf, indent=4)
    
    __analyze_schedule_results(
        triggers_m, 
        result_dir,
        invocation_start,
        invocation_end,
        prefix="experiments_scheduled")
    
def __convert_str_to_timestamp(ts: str):
    seconds, microseconds = ts.split(".")
    seconds = int(seconds)
    microseconds = int(float('0.' + microseconds) * 1e6)
    dt = datetime.fromtimestamp(seconds)
    dt = dt + timedelta(microseconds=microseconds)
    return dt

def __convert_unix_to_timestamp(ts: int):
    # originally in nanosecond precision
    seconds = ts // 1e9
    nanoseconds = ts % 1e9
    microseconds = nanoseconds // 1e3
    dt = datetime.fromtimestamp(seconds)
    dt = dt + timedelta(microseconds=microseconds)
    return dt
    
    
def __analyze_schedule_results(
    triggers_m: dict, 
    result_dir: str,
    client_start: int,
    client_end: int,
    prefix: str,
    ):
    """Calculates the following metrics
    From the main schedule script, we obtained the following metrics:
    1. actual scheduled duration

    We are interested in the following metrics
    1. 

    Func request -> queued -> Func invocation

    """
    result_f = open(os.path.join(result_dir, "results_log.txt"), "w")
    # Actual scheduling
    result_f.write("Done with schedule experiment\n")
    result_f.write(f"Start =  {client_start}\n")
    result_f.write(f"End   =  {client_end}\n")
    result_f.write(f"Actual scheduled duration was {(client_end-client_start)/1_000_000_000} seconds.\n")
    
    # Obtain actual invocation per second for experiment
    earliest_invocation_start = None
    latest_invocation_end = None
    successful_invocations = 0
    failed_invocations = 0
    
    # Overall metrics for plotting stacked bar chart
    benchmarks = []
    overall_queueing_latencies = []
    overall_initialization_latencies = []
    overall_execution_latencies = []
    total_num_warm = 0
    total_num_cold = 0
    
    # Benchmark specific metric
    for benchmark in triggers_m.keys():
        with open(os.path.join(result_dir, f"{prefix}_{benchmark}.json")) as outf:
            json_dict = json.load(outf)
        result_f.write("***********************************************\n")
        result_f.write(f"Statistics for {benchmark}\n")
        result_f.write(f"{triggers_m[benchmark]['success']} successes\n")
        result_f.write(f"{triggers_m[benchmark]['failure']} failures\n")
        successful_invocations += triggers_m[benchmark]['success']
        failed_invocations += triggers_m[benchmark]['failure']
        
        queueing_latencies = []  # in milliseconds
        initialization_latencies = []  # in milliseconds
        function_execution_durations = []  # in milliseconds
        end_to_end_latencies = []  # in milliseconds
        num_warm = 0
        num_cold = 0
        # If somehow not in _invocations
        if len(json_dict["_invocations"].keys()) == 0:
            print(f"No invocations for {benchmark}.")
            continue
        benchmarks.append(benchmark)
        # Will only have one invocations key
        invocation_key = list(json_dict["_invocations"].keys())[0]
        
        for key in json_dict["_invocations"][invocation_key].keys():
            sub_result = json_dict["_invocations"][invocation_key][key]
            if "request_id" not in sub_result["output"].keys():
                print(f"Ignoring failure w/o request id")
                continue
            times = sub_result["times"]
            
            queueing_latency = times["waitTime"]
            init_time = 0
            
            queueing_latencies.append(queueing_latency)
            
            if "initTime" in times:
                init_time = times["initTime"]
                num_cold += 1
            else:
                num_warm += 1
            initialization_latencies.append(init_time)
            
            # Both are in string
            invocation_began = __convert_str_to_timestamp(sub_result["output"]["begin"])
            client_end = __convert_str_to_timestamp(sub_result["output"]["end"])
            
            if earliest_invocation_start is None or invocation_began < earliest_invocation_start:
                earliest_invocation_start = invocation_began
            if latest_invocation_end is None or client_end > latest_invocation_end:
                latest_invocation_end = client_end
                
            function_duration = int((client_end - invocation_began) / timedelta(milliseconds=1))
            function_execution_durations.append(function_duration)
            
            end_to_end_latency = queueing_latency + init_time + function_duration
            end_to_end_latencies.append(end_to_end_latency)
            
        
        queueing_latencies = np.array(queueing_latencies)
        initialization_latencies = np.array(initialization_latencies)
        function_execution_durations = np.array(function_execution_durations)
        end_to_end_latencies = np.array(end_to_end_latencies)
        result_f.write(f"Average queueing latency: {np.mean(queueing_latencies)}\n")
        result_f.write(f"Average initialization latency: {np.mean(initialization_latencies)}\n")
        result_f.write(f"Average function execution: {np.mean(function_execution_durations)}\n")
        result_f.write(f"Num warm: {num_warm}\n")
        result_f.write(f"Num cold: {num_cold}\n")
        result_f.write(f"End to end latency: {np.mean(end_to_end_latencies)}\n")
        result_f.write("***********************************************\n")
        
        overall_queueing_latencies.append(np.mean(queueing_latencies))
        overall_initialization_latencies.append(np.mean(initialization_latencies))
        overall_execution_latencies.append(np.mean(function_execution_durations))
        total_num_warm += num_warm
        total_num_cold += num_cold

    # Actual requests/sec
    result_f.write(f"Actual invocation start: {earliest_invocation_start}\n")
    result_f.write(f"Actual invocation end: {latest_invocation_end}\n")
    
    total = successful_invocations + failed_invocations
    percent_succ = float(successful_invocations/total * 100)
    percent_fail = float(failed_invocations/total * 100)
    
    result_f.write(f"Num successful invocations {successful_invocations}\n")
    result_f.write(f"% successful invocations {percent_succ:.3f}\n")
    result_f.write(f"Num failed invocations {failed_invocations}\n")
    result_f.write(f"% failed invocations {percent_fail:.3f}\n")
    
    result_f.write(f"Num warm invocations {total_num_warm}\n")
    result_f.write(f"Num cold invocations {total_num_cold}\n")
    result_f.write(f"% Warm invocations {total_num_warm/(total_num_warm + total_num_cold) * 100.0}\n")
    
    invocation_delta = int((latest_invocation_end - earliest_invocation_start) / timedelta(seconds=1))
    result_f.write(f"Actual invocations/second: {successful_invocations / invocation_delta}\n")
    result_f.close()
    plot_function_breakdown(benchmarks,
                            overall_queueing_latencies,
                            overall_initialization_latencies,
                            overall_execution_latencies,
                            result_dir)  


def plot_function_breakdown(
    benchmarks,
    overall_queueing_latencies,
    overall_initialization_latencies,
    overall_execution_latencies,
    result_dir
):
    bars = {
        "Queueing": np.array(overall_queueing_latencies),
        "Initialization": np.array(overall_initialization_latencies),
        "Execution": np.array(overall_execution_latencies)
    }
    
    fig, ax = plt.subplots()
    bottom = np.zeros(len(benchmarks))
    width = 0.5
    for label, times in bars.items():
        p = ax.bar(benchmarks, times, width, label=label, bottom=bottom)
        bottom += times
    ax.set_title("Timing breakdown per benchmark")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.autofmt_xdate()
    plt.show()
    plt.savefig(os.path.join(result_dir, "results.png"), bbox_inches="tight", dpi=100)

def _split_schedule(n: int, root_schedule: ScheduleConfig):
    """
    Split the schedule into n workers
    We use a simple round robin distribution to distribute the schedule uniformly.
    This could be changed to some more sophisticated distribution
    """
    schedules = [[] for _ in range(n)]
    for i, so in enumerate(root_schedule.schedule):
        idx = i % n
        schedules[idx].append(so)
    return schedules

def worker_thread(idx: int, triggers: dict, schedule: List[ScheduleObject], queue: Queue):
    """Closed loop worker thread with latency correction"""
    # Scheduling worker loop
    invocation_start = time.time_ns()
    counters = {}  # dict of success/failure counter
    rets = {}  # dict of ExecutionResult
    for fn_name in triggers.keys():
        counters[fn_name] = {
            "success": 0,
            "failure": 0
        }
        rets[fn_name] = []
    for i, so in enumerate(schedule):
        now = time.time_ns()
        scheduled_time = invocation_start + so.timestamp
        waiting_time = 0
        if scheduled_time > now:
            # We are on track, so sleep until desired time
            delta_s = (scheduled_time - now) / 1_000_000_000
            time.sleep(delta_s)
        else:
            # scheduled_time <= now
            # We are behind, so we need to account that in our latency
            waiting_time = now - scheduled_time
        trigger = triggers[so.fn_name]["trigger"]
        input_config = triggers[so.fn_name]["input"]
        
        # Modified to return OpenWhisk wrapper
        ret = trigger.sync_invoke(input_config)
        try:
            if ret.executionResult.stats.failure:
                counters[so.fn_name]["failure"] += 1
            else:
                # TODO: Is this actually correct?
                ret.executionResult.times.latencyCorrection = waiting_time
                counters[so.fn_name]["success"] += 1
        except KeyError as e:
            print(f"key error with {so.fn_name}")
            print("All keys are ")
            for key in counters.keys():
                print(key)
        rets[so.fn_name].append(ret.executionResult)
    print(f"Worker {idx} is done with schedule.")
    invocation_end = time.time_ns()
    return_dict = {
        "ret": rets,
        "counter": counters,
        "worker_start": invocation_start,
        "worker_end": invocation_end,
    }
    queue.put(return_dict)


@cli.group()
def open_close():
    pass

"""
Run an open-closed workload.
Workers == threads that send invocation requests to Openwhisk
"""
@open_close.command()
@click.option(
    "--schedule_config", 
    type=str, 
    default="schedule.json", 
    help="path to schedule"
)
@click.option(
    "--n_workers", 
    type=int, 
    default=10, 
    help="Number of worker threads to spawn"
)
@click.option(
    "--trigger_t",
    type=click.Choice(["library"]),
    default="library",  
    help="Function trigger to be used.",
)
@click.option(
    "--memory",
    default=None,
    type=int,
    help="Override default memory settings for the benchmark function.",
)
@click.option(
    "--timeout",
    default=None,
    type=int,
    help="Override default timeout settings for the benchmark function.",
)
@click.option(
    "--result_dir",
    default="schedule-results",
    type=str,
    help="Results directory"
)
@common_params
def open_close(
    schedule_config,
    n_workers,
    trigger_t,
    memory,
    timeout,
    result_dir,
    **kwargs,
):
    # Universal common set up
    (
        config,
        output_dir,
        logging_filename,
        sebs_client,
        deployment_client,
    ) = parse_common_params(**kwargs)
    
    experiment_config = sebs_client.get_experiment_config(config["experiments"])
    
    if os.path.exists(result_dir):
        shutil.rmtree(result_dir)
    os.mkdir(result_dir)
    # Load schedule config
    with open(schedule_config, "r") as fp:
        schedule_config = json.load(fp)
    schedule_config = sebs_client.get_schedule_config(schedule_config)
    
    # Set up each benchmark trigger here
    # We differ from open schedule here because we don't want to create n copies of the benchmark obj
    triggers_m = {}
    for benchmark in schedule_config.fns:
        update_nested_dict(config, ["experiments", "benchmark"], benchmark)
        benchmark_obj = sebs_client.get_benchmark(
            benchmark,
            deployment_client,
            experiment_config,
            logging_filename=logging_filename
        )
        if memory is not None:
            benchmark_obj.benchmark_config.memory = memory
        if timeout is not None:
            benchmark_obj.benchmark_config.timeout = timeout

        func = deployment_client.get_function(
            benchmark_obj,
            deployment_client.default_function_name(benchmark_obj),
        )
        storage = deployment_client.get_storage(replace_existing=experiment_config.update_storage)
        input_config = benchmark_obj.prepare_input(storage=storage, size="small")
        
        result = sebs.experiments.ExperimentResult(experiment_config, deployment_client.config)
        result.begin()
        
        trigger_type = Trigger.TriggerType.get(trigger_t)
        triggers = func.triggers(trigger_type)
        if len(triggers) == 0:
            trigger = deployment_client.create_trigger(func, trigger_type)
        else:
            trigger = triggers[0]
        print(f"{benchmark=}")
        triggers_m[benchmark] = {}
        triggers_m[benchmark]["trigger"] = trigger
        triggers_m[benchmark]["function"] = func
        triggers_m[benchmark]["input"] = input_config
        triggers_m[benchmark]["result"] = result
    # Split the schedule among the n worker threads
    schedules = _split_schedule(n_workers, schedule_config)
    result_queue = Queue(maxsize=n_workers)
    workers = []
    for i in range(n_workers):
        p = Process(target=worker_thread, args=(i, triggers_m, schedules[i], result_queue))
        workers.append(p)
        p.start()
    # We need to aggregate all results from each worker now
    for benchmark in triggers_m.keys():
        triggers_m[benchmark]["success"] = 0
        triggers_m[benchmark]["failure"] = 0
    # Worker invocation times
    earliest_client_begin = None
    latest_client_end = None
    for i in range(n_workers):
        return_dict = result_queue.get()
        
        client_start = return_dict["worker_start"]
        client_end = return_dict["worker_end"]
        if earliest_client_begin is None or client_start < earliest_client_begin:
            earliest_client_begin = client_start
        if latest_client_end is None or client_end > latest_client_end:
            latest_client_end = client_end
        
        rets = return_dict["ret"]   
        sub_counter = return_dict["counter"]
        for benchmark in triggers_m.keys():
            func = triggers_m[benchmark]["function"]
            for ret in rets[benchmark]:
                triggers_m[benchmark]["result"].add_invocation(func, ret)
            triggers_m[benchmark]["success"] += sub_counter[benchmark]["success"]
            triggers_m[benchmark]["failure"] += sub_counter[benchmark]["failure"]
    
    for p in workers:
        p.join()

    # Write all files
    for benchmark in triggers_m.keys():
        result = triggers_m[benchmark]["result"]
        
        result.end()  # This call is redundant, but just to make sure the time is non null
        result_file = os.path.join(result_dir, f"experiments_open_close_{benchmark}.json")
        with open(result_file, "w") as out_f:
            out_f.write(sebs.utils.serialize(result))
    
    __analyze_schedule_results(
        triggers_m,
        result_dir,
        earliest_client_begin,
        latest_client_end,
        prefix="experiments_open_close"
    )

@benchmark.command()
@common_params
def process(**kwargs):

    (
        config,
        output_dir,
        logging_filename,
        sebs_client,
        deployment_client,
    ) = parse_common_params(**kwargs)

    result_file = os.path.join(output_dir, "experiments.json")
    sebs_client.logging.info("Load results from {}".format(os.path.abspath(result_file)))
    with open(result_file, "r") as in_f:
        config = json.load(in_f)
        experiments = sebs.experiments.ExperimentResult.deserialize(
            config,
            sebs_client.cache_client,
            sebs_client.generate_logging_handlers(logging_filename),
        )

    for func in experiments.functions():
        deployment_client.download_metrics(
            func, *experiments.times(), experiments.invocations(func), experiments.metrics(func)
        )

    output_file = os.path.join(output_dir, "results.json")
    with open(output_file, "w") as out_f:
        out_f.write(sebs.utils.serialize(experiments))
    sebs_client.logging.info("Save results to {}".format(output_file))


@benchmark.command()
@click.argument(
    "benchmark-input-size", type=click.Choice(["test", "small", "large"])
)  # help="Input test size")
@click.option(
    "--benchmark-name",
    default=None,
    type=str,
    help="Run only the selected benchmark.",
)
@common_params
@click.option(
    "--cache",
    default=os.path.join(os.path.curdir, "regression-cache"),
    help="Location of experiments cache.",
)
@click.option(
    "--output-dir",
    default=os.path.join(os.path.curdir, "regression-output"),
    help="Output directory for results.",
)
def regression(benchmark_input_size, benchmark_name, **kwargs):
    # for regression, deployment client is initialized locally
    # disable default initialization
    (config, output_dir, logging_filename, sebs_client, _) = parse_common_params(
        initialize_deployment=False, **kwargs
    )
    regression_suite(
        sebs_client,
        config["experiments"],
        set((config["deployment"]["name"],)),
        config["deployment"],
        benchmark_name,
    )


@cli.group()
def storage():
    pass


@storage.command("start")
@click.argument("storage", type=click.Choice([StorageTypes.MINIO]))
@click.option("--output-json", type=click.Path(dir_okay=False, writable=True), default=None)
@click.option("--port", type=int, default=9000)
def storage_start(storage, output_json, port):

    import docker

    sebs.utils.global_logging()
    storage_type = sebs.SeBS.get_storage_implementation(StorageTypes(storage))
    storage_config, storage_resources = sebs.SeBS.get_storage_config_implementation(StorageTypes(storage))
    config = storage_config()
    resources = storage_resources()

    storage_instance = storage_type(docker.from_env(), None, resources, True)
    logging.info(f"Starting storage {str(storage)} on port {port}.")
    storage_instance.start(port)
    if output_json:
        logging.info(f"Writing storage configuration to {output_json}.")
        with open(output_json, "w") as f:
            json.dump(storage_instance.serialize(), fp=f, indent=2)
    else:
        logging.info("Writing storage configuration to stdout.")
        logging.info(json.dumps(storage_instance.serialize(), indent=2))
        
@storage.command("clear")
@click.argument("input-json", type=click.Path(exists=True, dir_okay=False, readable=True))
def clear_storage(input_json):
    
    sebs.utils.global_logging()
    with open(input_json, "r") as f:
        cfg = json.load(f)
        storage_type = cfg["type"]
        
        storage_cfg, storage_resources = sebs.SeBS.get_storage_config_implementation(storage_type)
        config = storage_cfg.deserialize(cfg)
        
        if "resources" in cfg:
            resources = storage_resources.deserialize(cfg["resources"])
        else:
            resources = storage_resources() 
        logging.info("Clearing all buckets")
        storage = sebs.SeBS.get_storage_implementation(storage_type).deserialize(config, None, resources)
        for bucket in storage.list_buckets():
            print(bucket is None)
            logging.info(bucket)

@storage.command("stop")
@click.argument("input-json", type=click.Path(exists=True, dir_okay=False, readable=True))
def storage_stop(input_json):

    sebs.utils.global_logging()
    with open(input_json, "r") as f:
        cfg = json.load(f)
        storage_type = cfg["type"]

        storage_cfg, storage_resources = sebs.SeBS.get_storage_config_implementation(storage_type)
        config = storage_cfg.deserialize(cfg)

        if "resources" in cfg:
            resources = storage_resources.deserialize(cfg["resources"])
        else:
            resources = storage_resources()

        logging.info(f"Stopping storage deployment of {storage_type}.")
        storage = sebs.SeBS.get_storage_implementation(storage_type).deserialize(config, None, resources)
        storage.stop()
        logging.info(f"Stopped storage deployment of {storage_type}.")


@cli.group()
def local():
    pass


@local.command()
@click.argument("benchmark", type=str)
@click.argument("benchmark-input-size", type=click.Choice(["test", "small", "large"]))
@click.argument("output", type=str)
@click.option("--deployments", default=1, type=int, help="Number of deployed containers.")
@click.option("--storage-configuration", type=str, help="JSON configuration of deployed storage.")
@click.option("--measure-interval", type=int, default=-1,
              help="Interval duration between memory measurements in ms.")
@click.option(
    "--remove-containers/--no-remove-containers",
    default=True,
    help="Remove containers after stopping.",
)
@simplified_common_params
def start(benchmark, benchmark_input_size, output, deployments, storage_configuration,
          measure_interval, remove_containers, **kwargs):
    """
    Start a given number of function instances and a storage instance.
    """

    (config, output_dir, logging_filename, sebs_client, deployment_client) = parse_common_params(
        ignore_cache=True, update_code=False, update_storage=False,
        deployment="local", storage_configuration=storage_configuration, **kwargs
    )
    deployment_client = cast(sebs.local.Local, deployment_client)
    deployment_client.remove_containers = remove_containers
    result = sebs.local.Deployment()
    result.measurement_file = deployment_client.start_measurements(measure_interval)

    experiment_config = sebs_client.get_experiment_config(config["experiments"])
    benchmark_obj = sebs_client.get_benchmark(
        benchmark,
        deployment_client,
        experiment_config,
        logging_filename=logging_filename,
    )
    storage = deployment_client.get_storage(replace_existing=experiment_config.update_storage)
    result.set_storage(storage)
    input_config = benchmark_obj.prepare_input(storage=storage, size=benchmark_input_size)
    result.add_input(input_config)

    for i in range(deployments):
        func = deployment_client.get_function(
            benchmark_obj, deployment_client.default_function_name(benchmark_obj)
        )
        result.add_function(func)

    # Disable shutdown of storage only after we succed
    # Otherwise we want to clean up as much as possible
    deployment_client.shutdown_storage = False
    result.serialize(output)
    sebs_client.logging.info(f"Save results to {os.path.abspath(output)}")


@local.command()
@click.argument("input-json", type=str)
@click.argument("output-json", type=str, default="memory_stats.json")
# @simplified_common_params
def stop(input_json, output_json, **kwargs):
    """
    Stop function and storage containers.
    """

    sebs.utils.global_logging()

    logging.info(f"Stopping deployment from {os.path.abspath(input_json)}")
    deployment = sebs.local.Deployment.deserialize(input_json, None)
    deployment.shutdown(output_json)
    logging.info(f"Stopped deployment from {os.path.abspath(input_json)}")


@cli.group()
def experiment():
    pass


@experiment.command("invoke")
@click.argument("experiment", type=str)  # , help="Benchmark to be launched.")
@common_params
def experiment_invoke(experiment, **kwargs):
    (
        config,
        output_dir,
        logging_filename,
        sebs_client,
        deployment_client,
    ) = parse_common_params(**kwargs)
    experiment = sebs_client.get_experiment(experiment, config["experiments"])
    experiment.prepare(sebs_client, deployment_client)
    experiment.run()


@experiment.command("process")
@click.argument("experiment", type=str)  # , help="Benchmark to be launched.")
@click.option("--extend-time-interval", type=int, default=-1)  # , help="Benchmark to be launched.")
@common_params
def experiment_process(experiment, extend_time_interval, **kwargs):
    (
        config,
        output_dir,
        logging_filename,
        sebs_client,
        deployment_client,
    ) = parse_common_params(**kwargs)
    experiment = sebs_client.get_experiment(experiment, config["experiments"])
    experiment.process(
        sebs_client, deployment_client, output_dir, logging_filename, extend_time_interval
    )


@cli.group()
def resources():
    pass


@resources.command("list")
@click.argument(
    "resource",
    type=click.Choice(["buckets", "resource-groups"])
)
@common_params
def resources_list(resource, **kwargs):

    (
        config,
        output_dir,
        logging_filename,
        sebs_client,
        deployment_client,
    ) = parse_common_params(**kwargs)

    if resource == "buckets":
        storage_client = deployment_client.get_storage(False)
        buckets = storage_client.list_buckets()
        sebs_client.logging.info("Storage buckets:")
        for idx, bucket in enumerate(buckets):
            sebs_client.logging.info(f"({idx}) {bucket}")

    elif resource == "resource-groups":

        if deployment_client.name() != "azure":
            sebs_client.logging.error("Resource groups are only supported on Azure!")
            return

        groups = deployment_client.config.resources.list_resource_groups(deployment_client.cli_instance)
        sebs_client.logging.info("Resource grup:")
        for idx, bucket in enumerate(groups):
            sebs_client.logging.info(f"({idx}) {bucket}")


@resources.command("remove")
@click.argument(
    "resource",
    type=click.Choice(["buckets", "resource-groups"])
)
@click.argument(
    "prefix",
    type=str
)
@click.option(
    "--wait/--no-wait",
    type=bool,
    default=True,
    help="Wait for completion of removal."
)
@click.option(
    "--dry-run/--no-dry-run",
    type=bool,
    default=False,
    help="Simulate run without actual deletions."
)
@common_params
def resources_remove(resource, prefix, wait, dry_run, **kwargs):

    (
        config,
        output_dir,
        logging_filename,
        sebs_client,
        deployment_client,
    ) = parse_common_params(**kwargs)

    storage_client = deployment_client.get_storage(False)
    if resource == "storage":

        buckets = storage_client.list_buckets()
        for idx, bucket in enumerate(buckets):

            if len(prefix) > 0 and not bucket.startswith(prefix):
                continue

            sebs_client.logging.info(f"Removing bucket: {bucket}")
            if not dry_run:
                storage_client.clean_bucket(bucket)
                storage_client.remove_bucket(bucket)

    elif resource == "resource-groups":

        if deployment_client.name() != "azure":
            sebs_client.logging.error("Resource groups are only supported on Azure!")
            return

        groups = deployment_client.config.resources.list_resource_groups(deployment_client.cli_instance)
        for idx, group in enumerate(groups):
            if len(prefix) > 0 and not group.startswith(prefix):
                continue

            sebs_client.logging.info(f"Removing resource group: {group}")
            deployment_client.config.resources.delete_resource_group(deployment_client.cli_instance, group, wait)

if __name__ == "__main__":
    cli()
