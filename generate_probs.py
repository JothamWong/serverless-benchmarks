import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("--candidates", help="Candidates file", default="candidates_out_1_14.json")
options = parser.parse_args()

with open(options.candidates, "r") as inf:
    # candidates
    cs = json.load(inf)
    
# Get the individual total counts
counts = {}
for c in cs.keys():
    counts[c] = int(sum(cs[c]))
# Now we normalize and round to int
total_counts = sum(counts.values())
for c in counts:
    counts[c] = round((counts[c] / total_counts) * 100)

with open("events.json", "w") as outf:
    json.dump(counts, outf)