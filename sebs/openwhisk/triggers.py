import concurrent.futures
import datetime
import json
import subprocess
from typing import Dict, List, Optional  # noqa
import time

from sebs.faas.function import ExecutionResult, NonBlockingExecutionResult, Trigger


class LibraryTrigger(Trigger):
    def __init__(self, fname: str, wsk_cmd: Optional[List[str]] = None):
        super().__init__()
        self.fname = fname
        if wsk_cmd:
            self._wsk_cmd = [*wsk_cmd, "action", "invoke", "--result", self.fname]
            # no --result means non-blocking
            self._nb_wsk_cmd = [*wsk_cmd, "action", "invoke", self.fname]
            self._wsk_get_cmd = [*wsk_cmd, "activation", "result"]

    @staticmethod
    def trigger_type() -> "Trigger.TriggerType":
        return Trigger.TriggerType.LIBRARY

    @property
    def wsk_cmd(self) -> List[str]:
        assert self._wsk_cmd
        return self._wsk_cmd

    @wsk_cmd.setter
    def wsk_cmd(self, wsk_cmd: List[str]):
        self._wsk_cmd = [*wsk_cmd, "action", "invoke", "--result", self.fname]
        
    @property
    def nb_wsk_cmd(self) -> List[str]:
        assert self._nb_wsk_cmd
        return self._nb_wsk_cmd
    
    @nb_wsk_cmd.setter
    def nb_wsk_cmd(self, wsk_cmd: List[str]):
        self._wsk_cmd = [*wsk_cmd, "action", "invoke", self.fname]
        
    @property
    def wsk_get_cmd(self) -> List[str]:
        assert self._wsk_get_cmd
        return self._wsk_get_cmd

    @staticmethod
    def get_command(payload: dict) -> List[str]:
        params = []
        for key, value in payload.items():
            params.append("--param")
            params.append(key)
            params.append(json.dumps(value))
        return params
    
    def parse_nb_results(self, nb_result: NonBlockingExecutionResult) -> ExecutionResult:
        # TODO: Block until result is done, possibly needed for super long running functions
        # but serverless fns by defn are short running so prob not needed
        command = self.wsk_get_cmd + [str(nb_result.request_id)]
        self.logging.info(f"Command is {' '.join(command)}")
        error = None
        try:
            # We loop because it is possible when we arrive here, the non-blocking
            # result hasn't even been scheduled yet
            while True:
                begin = datetime.datetime.now()
                # FIXME: `run` fails, have to use `call` and I have no idea why
                response = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
                end = datetime.datetime.now()
                parsed_response = response.stdout.decode("utf-8")
                if parsed_response != "":
                    break
                # Sleep for a bit to avoid calling a command which is doomed to fail
                time.sleep(0.125)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            end = datetime.datetime.now()
            error = e
            print(e)
        
        openwhisk_result = ExecutionResult.from_times(begin, end)
        if error is not None:
            self.logging.error("Invocation of {} failed!".format(self.fname))
            self.logging.error(error)
            openwhisk_result.stats.failure = True
            return openwhisk_result
        
        return_content = json.loads(parsed_response)
        openwhisk_result.parse_benchmark_output(return_content)
        return openwhisk_result
    
    def openwhisk_nonblocking_invoke(self, payload: Dict) -> NonBlockingExecutionResult:
        command = self.nb_wsk_cmd + self.get_command(payload)
        self.logging.info(f"Command is {' '.join(command)}")
        error = None
        try:
            begin = datetime.datetime.now()
            response = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            end = datetime.datetime.now()
            parsed_response = response.stdout.decode("utf-8")
            print(parsed_response)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            end = datetime.datetime.now()
            error = e
        
        if error is not None:
            self.logging.error("Invocation of {} failed!".format(self.fname))
            ret = NonBlockingExecutionResult()
            ret.failure = True
            return ret
                
        ret = NonBlockingExecutionResult.deserialize(parsed_response, begin, end)
        return ret

    def sync_invoke(self, payload: dict) -> ExecutionResult:
        command = self.wsk_cmd + self.get_command(payload)
        self.logging.info(f"Command is {' '.join(command)}")
        error = None
        try:
            begin = datetime.datetime.now()
            response = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            end = datetime.datetime.now()
            parsed_response = response.stdout.decode("utf-8")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            end = datetime.datetime.now()
            error = e

        openwhisk_result = ExecutionResult.from_times(begin, end)
        if error is not None:
            self.logging.error("Invocation of {} failed!".format(self.fname))
            openwhisk_result.stats.failure = True
            return openwhisk_result

        return_content = json.loads(parsed_response)
        openwhisk_result.parse_benchmark_output(return_content)
        return openwhisk_result

    def async_invoke(self, payload: dict) -> concurrent.futures.Future:
        pool = concurrent.futures.ThreadPoolExecutor()
        fut = pool.submit(self.sync_invoke, payload)
        return fut

    def serialize(self) -> dict:
        return {"type": "Library", "name": self.fname}

    @staticmethod
    def deserialize(obj: dict) -> Trigger:
        return LibraryTrigger(obj["name"])

    @staticmethod
    def typename() -> str:
        return "OpenWhisk.LibraryTrigger"


class HTTPTrigger(Trigger):
    def __init__(self, fname: str, url: str):
        super().__init__()
        self.fname = fname
        self.url = url

    @staticmethod
    def typename() -> str:
        return "OpenWhisk.HTTPTrigger"

    @staticmethod
    def trigger_type() -> Trigger.TriggerType:
        return Trigger.TriggerType.HTTP
    
    def parse_nb_results(self, nb_result: NonBlockingExecutionResult) -> ExecutionResult:
        raise ValueError("Openwhisk HTTP Trigger cannot support non-blocking invocation!")

    def openwhisk_nonblocking_invoke(self, payload: Dict) -> NonBlockingExecutionResult:
        raise ValueError("Openwhisk HTTP Trigger cannot support non-blocking invocation!")

    def sync_invoke(self, payload: dict) -> ExecutionResult:
        self.logging.debug(f"Invoke function {self.url}")
        return self._http_invoke(payload, self.url, False)

    def async_invoke(self, payload: dict) -> concurrent.futures.Future:
        pool = concurrent.futures.ThreadPoolExecutor()
        fut = pool.submit(self.sync_invoke, payload)
        return fut

    def serialize(self) -> dict:
        return {"type": "HTTP", "fname": self.fname, "url": self.url}

    @staticmethod
    def deserialize(obj: dict) -> Trigger:
        return HTTPTrigger(obj["fname"], obj["url"])
