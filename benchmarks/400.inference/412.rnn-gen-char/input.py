import os

# language : text(example: Italian, German, Portuguese, Chinese, Greek, Polish, French, English, Spanish, Arabic, Crech, Russian, Irish, Dutch, Scottish, Vietnamese, Korean, Japanese)

# start_letters : text (example: 'ABCDEFGHIJKLMNOP'

generator = {
    'test': ['English', 'ABC'],
    'small': ['English', 'ABCDEFGHIJKLMOPQRSTUVWXYZ'],
    'large': ['English', 'ABCDEFGHIJKLMOPQRSTUVWXYZ']
}

def input_generator(size):
    return generator[size]

def buckets_count():
    return (2, 0)

'''
    Generate test, small and large workload for rnn gen char test.

    :param data_dir: directory where benchmark data is placed
    :param size: workload size
    :param input_buckets: input storage containers for this benchmark
    :param output_buckets:
    :param upload_func: upload function taking three params(bucket_idx, key, filepath)
'''
def generate_input(data_dir, size, benchmarks_bucket, input_paths, output_paths, upload_func):
    # upload model
    model_name = 'rnn_model.pth'
    upload_func(0, model_name, os.path.join(data_dir, 'model', model_name))
    
    # upload parameters
    params_name = 'rnn_params.pkl'
    upload_func(1, params_name, os.path.join(data_dir, 'model', params_name))
    
    print(params_name)
    
    input_config = {'object': {}, 'bucket': {}}
    input_config['object']['model'] = model_name
    input_config['object']['input'] = params_name
    input_config['bucket']['bucket'] = benchmarks_bucket
    input_config['bucket']['input'] = input_paths[1]
    input_config['bucket']['model'] = input_paths[0]
    
    inputs = input_generator(size)
    
    input_config['language'] = inputs[0]
    input_config['start_letters'] = inputs[1]
    # input_config['all_categories'] = ['Arabic', 'Chinese', 'Czech', 'Dutch', 'English', 'French', 'German', 'Greek', 'Irish', 'Italian', 'Japanese', 'Korean', 'Polish', 'Portuguese', 'Russian', 'Scottish', 'Spanish', 'Vietnamese']
    # input_config['n_categories'] = 18
    # input_config['n_letters'] = 59
    # input_config['n_letters'] = 59
    
    return input_config
    