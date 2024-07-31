"""Generate text files of random sizes with increments of 1kB numbered"""
import argparse
import random
import string
import os
import shutil

from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument("--data_dst", type=str, default="random_text", help="default destination for folder")
parser.add_argument("--low", type=int, default=1, help="Lowest text size, in kilobytes")
parser.add_argument("--high", type=int, default=500, help="Highest text size, in kilobytes")
options = parser.parse_args()

if os.path.isdir(options.data_dst):
    shutil.rmtree(options.data_dst)
os.mkdir(options.data_dst)


def generate_random_string(length):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))

def create_random_file(filename, size_kb):
    chunk_size = 1024
    with open(filename, "w") as outf:
        for i in range(size_kb):
            chunk = generate_random_string(chunk_size)
            outf.write(chunk)


for i in tqdm(range(options.low, options.high + 1)):
    create_random_file(os.path.join(options.data_dst, f"{i}.txt"), i)