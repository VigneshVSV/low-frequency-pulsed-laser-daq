import os
import ssl
import logging
from device import HWTriggeredDevice
from hololinked.server import HTTPServer
from multiprocessing import Process

def start_https_server():
    # You need to create a certificate on your own 
    ssl_context = ssl.SSLContext(protocol = ssl.PROTOCOL_TLS)
    ssl_context.load_cert_chain(f'assets{os.sep}security{os.sep}certificate.pem',
                        keyfile = f'assets{os.sep}security{os.sep}key.pem')

    H = HTTPServer(['triggered-device-test'], port=8082, ssl_context=ssl_context)
    H.listen()


if __name__ == '__main__':
    P = Process(target=start_https_server, daemon=True) 
    # change to start_http_server if no certificate available
    P.start()

    HWTriggeredDevice(instance_name='triggered-device-test', 
                    log_level=logging.DEBUG).run()
    