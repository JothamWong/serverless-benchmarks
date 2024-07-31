import datetime
import numpy as np

def handler(event):
    
    n = event.get('size')
    matrix_generation_start = datetime.datetime.now()
    A = np.random.rand(n, n)
    B = np.random.rand(n, n)
    matrix_generation_end = datetime.datetime.now()
    calculation_start = datetime.datetime.now()
    C = np.matmul(A, B)
    calculation_end = datetime.datetime.now()
    
    matrix_generation_time = (matrix_generation_end - matrix_generation_start) / datetime.timedelta(microseconds=1)
    calculation_time = (calculation_end - calculation_start) / datetime.timedelta(microseconds=1)
    
    return {
        'result': "",  # We don't care
        'measurement': {
            'matrix_generating_time': matrix_generation_time,
            'compute_time': calculation_time
        }
    }