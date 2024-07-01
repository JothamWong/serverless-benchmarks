import math
import sys


if len(sys.argv) != 3:
    print(f"Usage: python {sys.argv[0]} [n_invokers] [memory]")

num_invoker_instances = int(sys.argv[1])
mem = int(sys.argv[2])  # in MB for containerpool setting

# assume each container is 128MB (by default)
container_size = 128
max_concurrency = math.floor((num_invoker_instances * mem) / container_size)

print(f"Num invoker instances          = {num_invoker_instances}")
print(f"Memory for each container pool = {mem}MB")
print(f"Max concurrency                =  {max_concurrency}")