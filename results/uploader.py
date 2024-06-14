import json


cwd = "/mnt/sdb/home/Jotham/serverless-benchmarks/results"
zip_count = 0
jpg_count = 0
pth_count = 0

with open(f"{cwd}/120.uploader.results.json", "r") as inf:
    exp = json.load(inf)
    subexp_name = list(exp['_invocations'].keys())[0]  # guaranteed only one
    for activation_id in exp['_invocations'][subexp_name].keys():
        filename = exp['_invocations'][subexp_name][activation_id]['output']['result']['result']['url']
        if filename.endswith(".jpg"):
            jpg_count += 1
        elif filename.endswith(".pth"):
            pth_count += 1
        elif filename.endswith(".zip"):
            zip_count += 1
        else:
            raise ValueError("Unaccounted file type")

print(f"{zip_count=}")
print(f"{jpg_count=}")
print(f"{pth_count=}")