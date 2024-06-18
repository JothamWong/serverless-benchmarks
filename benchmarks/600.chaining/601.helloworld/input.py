line_generators = {
    'test': 'Over-ripe sushi,\nThe Master\nIs full of regret.',
    'small': 'Over-ripe sushi,\nThe Master\nIs full of regret.',
    'large': 'Over-ripe sushi,\nThe Master\nIs full of regret.',
}

def buckets_count():
    return (0, 0)

def generate_input(data_dir, size, benchmarks_bucket, input_paths, output_paths, upload_func):
    return { 'line': line_generators[size] }
