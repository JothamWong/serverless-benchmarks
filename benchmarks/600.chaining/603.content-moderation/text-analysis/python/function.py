import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

import os
import uuid
import datetime

from . import storage
client = storage.storage.get_instance()

def handler(event):
    bucket = event.get("bucket_name")
    txt_key = event.get("txt_key")
    download_path = event.get("download_path")
    
    s3_download_begin = datetime.datetime.now()
    client.download(bucket, txt_key, download_path)
    s3_download_end = datetime.datetime.now()
    
    nltk_download_begin = datetime.datetime.now()
    nltk.download('vader_lexicon')
    nltk_download_end = datetime.datetime.now()
    
    with open(download_path, "r") as f:
        txt = f.readline()
    
    nltk_process_begin = datetime.datetime.now()    
    sia = SentimentIntensityAnalyzer()
    sentiment_scores = sia.polarity_scores(txt)
    nltk_process_end = datetime.datetime.now()    
    
    if sentiment_scores["compound"] >= 0.05:
        sentiment = "Positive"
    elif sentiment_scores["compound"] <= -0.05:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"
        
    s3_download_time = (s3_download_end - s3_download_begin) / datetime.timedelta(microseconds=1)
    nltk_download_time = (nltk_download_end - nltk_download_begin) / datetime.timedelta(microseconds=1)
    nltk_process_time = (nltk_process_end - nltk_process_begin) / datetime.timedelta(microseconds=1)
        
    return {
        "result": {
            "sentiment": sentiment,
        },
        "measurement": {
            "second_s3_download_time": s3_download_time,
            "nltk_download_time": nltk_download_time,
            "nltk_process_time": nltk_process_time,
        }
    }