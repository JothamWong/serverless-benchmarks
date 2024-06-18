import datetime

def handler(event):

    line = event.get('line')

    start = datetime.datetime.now()
    lines = line.split()
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
