import datetime
import string
import random
import pyaes

def generate(length):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def handler(event):

    size = event.get('size')

    msg_generating_begin = datetime.datetime.now()
    message = generate(size)
    msg_generating_end = datetime.datetime.now()
    
    # 128-bit key (16 bytes)
    KEY = b'\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,'
    
    aes_start = datetime.datetime.now()
    aes = pyaes.AESModeOfOperationCTR(KEY)
    ciphertext = aes.encrypt(message)
    aes = pyaes.AESModeOfOperationCTR(KEY)
    plaintext = aes.decrypt(ciphertext)
    aes_end = datetime.datetime.now()

    msg_generating_time = (msg_generating_end - msg_generating_begin) / datetime.timedelta(microseconds=1)
    process_time = (aes_end - aes_start) / datetime.timedelta(microseconds=1)

    return {
            'result': {
                'plaintext': plaintext.decode(),
            },
            'measurement': {
                'msg_generating_time': msg_generating_time,
                'compute_time': process_time
            }
    }
