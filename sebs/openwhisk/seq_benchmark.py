"""
Creates code packages representing a sequence benchmark with all code and assets prepared
and dependencies installed performed within Docker image corresponding to Openwhisk deployment.

The behavior of the class is fundamentally the same as the Benchmark class
1. For each action in the sequence, call it Action Benchmark
    1.  If there is no cache entry, a code package is built.
    2.  Otherwise, the hash of the action benchmark is computed and compared with the cached
        value. If changed, rebuild then benchmark.
    3.  Otherwise, return the path to cache code.
"""

import glob
import hashlib
import json
import os
import shutil
import subprocess
from abc import abstractmethod
from typing import Any, Callable, Dict, List, Tuple, Optional

import docker

from sebs.config import SeBSConfig
from sebs.cache import Cache
from sebs.faas.config import Resources
from sebs.utils import find_benchmark, project_absolute_path, LoggingBase
from sebs.faas.storage import PersistentStorage
from sebs.benchmark import Benchmark, BenchmarkConfig, load_benchmark_input
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sebs.experiments.config import Config as ExperimentConfig
    from sebs.faas.function import Language

class SequenceBenchmark(LoggingBase):
    @staticmethod
    def typename() -> str:
        return "SequenceBenchmark"
    
    @property
    def benchmark(self):
        return self._benchmark
    
    @property
    def benchmark_path(self):
        return self._benchmark_path
    
    @property
    def benchmark_config(self) -> BenchmarkConfig:
        return self._benchmark_config
    
    @property
    def language(self) -> "Language":
        return self._language
    
    @property
    def language_name(self) -> str:
        return self._language.value
    
    @property
    def language_version(self) -> str:
        return self._language_version
    
    @property
    def code_package(self) -> dict:
        return self._code_package
    
    @property
    def code_location(self):
        if self.code_package:
            return os.path.join(self._cache_client.cache_dir, self.code_package["location"])
        else:
            return self._code_location
        
    @property
    def code_size(self):
        return self._code_size
        
    @property
    def functions(self) -> Dict[str, Any]:
        return self._functions
    
    @property  # noqa: A003
    def hash(self):
        path = os.path.join(self.benchmark_path, self.language_name)
        self._hash_value = Benchmark.hash_directory(path, self._deployment_name, self.language_name)
        return self._hash_value

    @hash.setter  # noqa: A003
    def hash(self, val: str):
        """
        Used only for testing purposes.
        """
        self._hash_value = val
    
    def __init__(
        self,
        benchmark: str,
        deployment_name: str,
        config: "ExperimentConfig",
        system_config: SeBSConfig,
        output_dir: str,
        cache_client: Cache,
        docker_client: docker.client,
        benchmark_config: BenchmarkConfig,
    ):
        super().__init__()
        print("Using SequenceBenchmark")
        self._benchmark = benchmark
        self._deployment_name = deployment_name
        self._experiment_config = config
        self._language = config.runtime.language
        self._language_version = config.runtime.version
        self._benchmark_path = find_benchmark(self.benchmark, "benchmarks")
        self._benchmark_config = benchmark_config
        if self.language not in self.benchmark_config.languages:
            raise RuntimeError(
                "Benchmark {} not available for language {}".format(self.benchmark, self.language)
            )
        print(f"OUTPUT DIR IN SEQ BENCH IS {output_dir=}")
        self._cache_client = cache_client
        self._docker_client = docker_client
        self._system_config = system_config
        self._hash_value = None
        self._output_dir = os.path.join(
            output_dir, f"{benchmark}_code", self._language.value, self._language_version
        )
        # Assumed to be done in order
        self.actions = [
            Benchmark(
                benchmark=action,
                deployment_name=deployment_name,
                config=config,
                system_config=system_config,
                output_dir=self._output_dir,  # Note this change
                cache_client=cache_client,
                docker_client=docker_client,
            ) for action in self._benchmark_config.wsk_sequence
        ]
        # Check if all cached
        self._is_cached = all(action.is_cached for action in self.actions)
        self._is_cached_valid = all(action.is_cached_valid for action in self.actions)
        self._code_package = self._cache_client.get_code_package(
            deployment=self._deployment_name,
            benchmark=self._benchmark,
            language=self.language.name,
            language_version=self._language_version
        )
        self._functions = self._cache_client.get_functions(
            deployment=self._deployment_name,
            benchmark=self._benchmark,
            language=self.language.name
        )
        print(f"Inside sequence {self._functions=}")
        if config.update_code:
            self._is_cached_valid = False
        
    
    def build(
        self, deployment_build_step: Callable[[str, str, str, str, bool], Tuple[str, int]]
    ) -> Tuple[bool, str]:
        print("BUILD METHOD FOR SEQ")
        if self._is_cached and self._is_cached_valid:
            self.logging.info("Using cached benchmark {} at {}".format(self.benchmark, self.code_location))
        # openwhisk_sequence entails creating multiple actions, each with diff subfolder
        # going to assume all stuff are the same at the moment, may be more complex
        # and need to rewrite later (?) 
        # Test poc first
        self._code_location = []
        self._code_size = 0
        for seq, action in enumerate(self.actions):
            # Decorate the original action add_deployment to call the sequence
            # deployment file afterwards
            action.action_seq_no = seq
            action.final_seq_no = len(self.actions) - 1
            action.add_deployment_files = action.add_seq_deployment_files
            _, code_location = action.build(deployment_build_step)
            self._code_location.append(code_location)
            self._code_size += os.path.getsize(code_location)
            
        self.logging.info("Creating cache entry")
        # self._cache_client.add_code_package(self._deployment_name, self.language_name, self)
        self._cache_client.add_sequence_package(self._deployment_name, self.language_name, self)
        print("DONE WITH BUILD")
        return True, self._code_location
    
    def serialize(self) -> dict:
        return {"size": self.code_size, "hash": self.hash}
    
    def recalculate_code_size(self):
        self._code_size = Benchmark.directory_size(self._output_dir)
        return self._code_size
    
    def prepare_input(self, storage: PersistentStorage, size: str):
        print("Inside prepare_input")
        benchmark_data_path = find_benchmark(self._benchmark, "benchmarks-data")
        mod = load_benchmark_input(self._benchmark_path)

        buckets = mod.buckets_count()
        input, output = storage.benchmark_data(self.benchmark, buckets)

        # buckets = mod.buckets_count()
        # storage.allocate_buckets(self.benchmark, buckets)
        # Get JSON and upload data as required by benchmark
        input_config = mod.generate_input(
            benchmark_data_path,
            size,
            storage.get_bucket(Resources.StorageBucketType.BENCHMARKS),
            input,
            output,
            storage.uploader_func,
        )

        # self._cache_client.update_storage(
        #     storage.deployment_name(),
        #     self._benchmark,
        #     {
        #         "buckets": {
        #             "input": storage.input_prefixes,
        #             "output": storage.output_prefixes,
        #             "input_uploaded": True,
        #         }
        #     },
        # )

        return input_config
            
def decorate_action_deployment(action: Benchmark, seq: int):
    def add_deployment_files(self: Benchmark, output_dir: str):
        handlers_dir = project_absolute_path("benchmarks", "wrappers", self._deployment_name, self.language_name)
        handlers = [
            os.path.join(handlers_dir, file)
            for file in self._system_config.deployment_files(
                self._deployment_name, self.language_name
            )
        ]
        print("INSIDE HAX")
        for file in handlers:
            print(file)
            ...
        raise NotImplementedError()
    return add_deployment_files


        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        