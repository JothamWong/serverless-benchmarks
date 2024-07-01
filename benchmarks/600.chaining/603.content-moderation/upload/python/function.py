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
    output_prefix = event.get('bucket').get('output')
    key = event.get('object').get('key')
    download_path = '/tmp/{}-{}'.format(key, uuid.uuid4())
    
    text_size = os.path.getsize(download_path)
    
    s3_download_begin = datetime.datetime.now()
    client.download(bucket, os.path.join(input_prefix, key), download_path)
    s3_download_stop = datetime.datetime.now()
    
    # Make the bucket if it does not exist
    bucket_name = "content-moderation-bucket"
    found = client.client.bucket_exists(bucket_name)
    if not found:
        client.client.make_bucket(bucket_name)
    
    s3_upload_begin = datetime.datetime.now()
    key_name = client.upload(bucket_name, key, download_path)
    s3_upload_stop = datetime.datetime.now()
    
    download_time = (s3_download_stop - s3_download_begin) / datetime.timedelta(microseconds=1)
    upload_time = (s3_upload_stop - s3_upload_begin) / datetime.timedelta(microseconds=1)
    
    return {
        'result': {
            'bucket_name': bucket_name,
            'download_path': download_path,
            'txt_key': key_name,
            "text_size": text_size
        },
        'measurement': {
            'initial_download_time': download_time,
            'initial_upload_time': upload_time,
        }
    }