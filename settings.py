import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'libs'))
from SocksiPy import socks
from datetime import datetime

# zheng.im
SERVER_ADDRESS = '138.68.58.173'
#CLIENT_ADDRESS = None
SERVER_TO_CLIENT_PORT = 8964
#CORRUPT_TOR_ADDRESS = '54.186.184.40'
TOR_SERVER_PORT = 8080
SERVER_TO_TOR_PORT = 6489
FINGERPRINTS = ['7B3F666CD6665CFF146F61CE005DD19F89DBC23A', '0DDDAAF2FCE825D286D70E99F70BB85FE12660C4', '15999A15088C133AF85AAF73DB74AC5C7B28114D', '7FBD5CCE31EAC5CED96F88ACA9D69656DA75CDF7', 'D4317592208BCB6EDA4572BBB66D4E7913DDAB49']

SOCKS_TYPE = socks.PROXY_TYPE_SOCKS5
SOCKS_HOST = '127.0.0.1'
CONNECTION_TIMEOUT = 30  # timeout before we give up on a circuit


class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    SUCCESS = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'


def success(msg):
    sys.stdout.write(Color.SUCCESS + "{0} {1}\n".format(datetime.utcnow(), msg) +
                     Color.END)
    sys.stdout.flush()


def warning(msg):
    sys.stdout.write(Color.WARNING + "{0} {1}\n".format(datetime.utcnow(), msg) +
                     Color.END)
    sys.stdout.flush()


def failure(msg):
    sys.stdout.write(Color.FAIL + "{0} [ERROR] {1}\n".format(datetime.utcnow(),
                                                             msg) + Color.END)
    sys.stdout.flush()
    sys.exit(-1)


def log(msg):
    sys.stdout.write("{0} {1}\n".format(datetime.utcnow(), msg))
    sys.stdout.flush()
