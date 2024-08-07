import os
import datetime

import torch

import pickle
from . import rnn
from . import storage
client = storage.storage.get_instance()

model = None

def handler(event):
    bucket = event.get('bucket').get('bucket')
    input_prefix = event.get('bucket').get('input')
    model_prefix = event.get('bucket').get('model')
    params_key = event.get('object').get('input')
    model_key = event.get('object').get('model')

    language = event.get('language')
    start_letters = event.get('start_letters')
    
    global model
    if not model:
        model_download_begin = datetime.datetime.now()
        model_path = os.path.join('/tmp', model_key)
        client.download(bucket, os.path.join(model_prefix, model_key), model_path)
        model_download_end = datetime.datetime.now()
        
        params_download_begin = datetime.datetime.now()
        params_path = os.path.join('/tmp', params_key)
        client.download(bucket, os.path.join(input_prefix, params_key), params_path)
        params_download_end = datetime.datetime.now()
        
        with open(params_path, 'rb') as pkl:
            params = pickle.load(pkl)
        
        all_categories = params['all_categories']
        n_categories = params['n_categories']
        all_letters = params['all_letters']
        n_letters = params['n_letters']
        
        model_process_begin = datetime.datetime.now()
        model = rnn.RNN(n_letters, 128, n_letters, all_categories, n_categories, all_letters, n_letters)
        model.load_state_dict(torch.load(model_path))
        model.eval()
        model_process_end = datetime.datetime.now()
    else:
        model_download_begin = datetime.datetime.now()
        model_download_end = model_download_begin
        params_download_begin = datetime.datetime.now()
        params_download_end = params_download_begin
        model_process_begin = datetime.datetime.now()
        model_process_end = model_process_begin
    
    process_begin = datetime.datetime.now()
    output_names = list(model.samples(language, start_letters))
    process_end = datetime.datetime.now()
    
    model_download_time = (model_download_end - model_download_begin) / datetime.timedelta(microseconds=1)
    params_download_time = (params_download_end - params_download_begin) / datetime.timedelta(microseconds=1)
    model_process_time = (model_process_end - model_process_begin) / datetime.timedelta(microseconds=1)
    process_time = (process_end - process_begin) / datetime.timedelta(microseconds=1)
    return {
        'result': {'output_names': output_names},
        'measurement': {
            'download_time': model_download_time + params_download_time,
            'model_download_time': model_download_time,
            'params_download_time': params_download_time,
            'compute_time': model_process_time + process_time,
            'model_process_time': model_process_time,
            'process_time': process_time
        }
    }
    