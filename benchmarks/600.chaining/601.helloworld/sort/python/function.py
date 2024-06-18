import datetime

def handler(event):

    lines = event.get('lines')

    start = datetime.datetime.now()
    lines = sorted(lines)
    end = datetime.datetime.now()

    process_time = (end - start) / datetime.timedelta(microseconds=1)

    return {
            'result': {
                'lines': lines    
            },
            'measurement': {
                'compute_time': process_time
            }
    }
