import logging, ssl, os, sys 
from multiprocessing import Process

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from hololinked.server import HTTPServer
from things.pico.device import Picoscope


def start_https_server():
    # You need to create a certificate on your own 
    ssl_context = ssl.SSLContext(protocol = ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(f'assets{os.sep}security{os.sep}certificate.pem',
                        keyfile = f'assets{os.sep}security{os.sep}key.pem')
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3

    H = HTTPServer(['picoscope'], port=9004, ssl_context=ssl_context, 
                      log_level=logging.DEBUG)  
    H.listen()


def multiprocess_example():
    P = Process(target=start_https_server) 
    # change to start_http_server if no certificate available
    P.start()

    Picoscope(
        instance_name='picoscope', 
        serial_number='CR524/015',
        log_level=logging.DEBUG
    ).run()


def multithreaded_example():
    ssl_context = ssl.SSLContext(protocol = ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(f'assets{os.sep}security{os.sep}certificate.pem',
                        keyfile = f'assets{os.sep}security{os.sep}key.pem')
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3

    Picoscope(
        instance_name='picoscope', 
        serial_number='CR524/015',
        log_level=logging.DEBUG
    ).run_with_http_server(
        port=9004, ssl_context=ssl_context, 
        log_level=logging.DEBUG
    )


if __name__ == '__main__':   
    multithreaded_example()