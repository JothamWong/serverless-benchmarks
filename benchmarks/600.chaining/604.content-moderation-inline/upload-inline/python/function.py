from minio import Minio
import uuid
import os
import datetime

from . import storage
client = storage.storage.get_instance()

def parse_directory(directory):
    size = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            size += os.path.getsize(os.path.join(root, file))
    return size


def handler(event):
    bucket = event.get('bucket').get('bucket')
    input_prefix = event.get('bucket').get('input')
    key = event.get('object').get('key')
    download_path = '/tmp/{}-{}'.format(key, uuid.uuid4())
    
    
    s3_download_begin = datetime.datetime.now()
    client.download(bucket, os.path.join(input_prefix, key), download_path)
    s3_download_stop = datetime.datetime.now()
    
    with open(download_path, "r") as inf:   
        text = "\n".join(inf.readlines())
    text_size = os.path.getsize(download_path)
        
    download_time = (s3_download_stop - s3_download_begin) / datetime.timedelta(microseconds=1)
    
    return {
        'result': {
            'txt': text,
            "text_size": text_size
        },
        'measurement': {
            'initial_download_time': download_time,
        }
    }