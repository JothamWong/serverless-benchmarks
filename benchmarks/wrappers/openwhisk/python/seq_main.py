import logging
import datetime
import os
import traceback

import minio

"""
This script is almost identical to the default __main__ except that
1. args now accepts numerical position in sequence
2. return value is not nested
"""

def main(args):
    logging.getLogger().setLevel(logging.INFO)
    begin = datetime.datetime.now()
    args['request-id'] = os.getenv('__OW_ACTIVATION_ID')
    args['income-timestamp'] = begin.timestamp()

    for arg in ["MINIO_STORAGE_CONNECTION_URL", "MINIO_STORAGE_ACCESS_KEY", "MINIO_STORAGE_SECRET_KEY"]:
        os.environ[arg] = args[arg]
        del args[arg]

    try:
        from function import function
        ret = function.handler(args)
        end = datetime.datetime.now()
        logging.info("Function result: {}".format(ret))

        results_time = (end - begin) / datetime.timedelta(microseconds=1)

        is_cold = False
        fname = "cold_run"
        if not os.path.exists(fname):
            is_cold = True
            open(fname, "a").close()
        
        # Get mem usage in KB
        with open('/proc/self/status') as f:
            memusage = int(f.read().split('VmRSS:')[1].split('\n')[0][:-3].strip())

        # Will be replaced at build time
        seq_number = {seq_number}
        final_seq = {final_seq}
        
        payload = {
            f"{seq_number}_begin": begin.strftime("%s.%f"),
            f"{seq_number}_end": end.strftime("%s.%f"),
            f"{seq_number}_request_id": os.getenv('__OW_ACTIVATION_ID'),
            f"{seq_number}_results_time": results_time,
            f"{seq_number}_is_cold": is_cold,
            f"{seq_number}_memusage": memusage,
            "result": {}
        }
        
        if "measurement" in ret:
            payload[f"{seq_number}_measurement"] = ret["measurement"]
            del ret["measurement"]
        
        if seq_number == 0:
            payload["request_id"] = os.getenv('__OW_ACTIVATION_ID')
            payload["is_cold"] = os.getenv('__OW_ACTIVATION_ID')
        else:
            # Flatten the arg
            for k, v in args.items():
                if str(seq_number - 1) in k:
                    payload[k] = v
            # We also need to pass results
            
        if seq_number == final_seq:
            # SeBS expects a result key
            payload["result"] = ret["result"]
            payload["request_id"] = args["0_request_id"]
            payload["is_cold"] = args["0_is_cold"]
            payload["begin"] = args["0_begin"]
            payload["end"] = payload["{final_seq}_end"]
        else:
            # Note: going to assume that by virtue of designing the benchmarks ourselves
            # we won't run into a problem where the function payload overrides some key metric
            payload = {**payload, **ret["result"]}

        return payload
    # Pass more detailed error trace, debugging serverless is painful
    except Exception as e:
        end = datetime.datetime.now()
        results_time = (end - begin) / datetime.timedelta(microseconds=1)
        return {
            "begin": begin.strftime("%s.%f"),
            "end": end.strftime("%s.%f"),
            "request_id": os.getenv('__OW_ACTIVATION_ID'),
            "results_time": results_time,
            "result": f"Error - invocation failed! Reason: {traceback.format_exc()}",
            "args": args
        }
