import StringIO
import time
import argparse
import sys
from datetime import datetime
import threading
import socket
import random

import stem.control
from stem.util import term
import stem.process
from stem.control import EventType
from stem import CircStatus, OperationFailed, InvalidRequest, InvalidArguments, CircuitExtensionFailed

from settings import *

SOCKS_PORT = 7000
CONTROLLER_PORT = 9051

circuit_id = None

class CorruptTorServer(threading.Thread):
    def __init__(self, port, controller):
        threading.Thread.__init__(self)
        socks.setdefaultproxy(SOCKS_TYPE, SOCKS_HOST, SOCKS_PORT)
        socket.socket = socks.socksocket
        self.controller = controller

    def get_socket(self):
        s = socks.socksocket()
        s.settimeout(CONNECTION_TIMEOUT)
        s.connect((SERVER_ADDRESS, SERVER_TO_TOR_PORT))
        return s

    def run(self):
        while True:
            global circuit_id
            path = [random.choice(FRINGPRINTS)]
            circuit_id = controller.new_circuit(path=path, await_build=True)
            time.sleep(1)
            for i in range(1000):
                print i
                s = self.get_socket()
                now = datetime.utcnow()
                timestamp = time.mktime(now.timetuple())
                data = '{} {}'.format(timestamp, now.microsecond)
                s.send(data)
                s.close()

print(term.format("Starting Tor:", term.Attr.BOLD))

tor_process = stem.process.launch_tor_with_config(
    config={
        'SocksPort':
        str(SOCKS_PORT),
        'ControlPort':
        str(CONTROLLER_PORT),
        'TestingTorNetwork':
        '1',
        #'__DisablePredictedCircuits': '1',
        #'MaxOnionsPending': '0',
        'newcircuitperiod':
        '999999999',
        'maxcircuitdirtiness':
        '999999999',
        #'AlternateDirAuthority': ['54.208.179.145:9030 60E6E78926A45A77C1CB6BCC59D459083CB8530F', '138.68.58.173:9030 1A19C6822777515982DAD87CD2AA65B071305A1E'],
        'DirServer': [
            'auth orport=5000 no-v2 v3ident=A9495BBC01F3B30247673A7C3253EDF21687468E 54.197.200.127:7000 584C 788B 916E 8C3D 12F1 F750 9199 9038 09A5 1CF7'
        ],
        'ClientOnly':
        '1',
        'AllowSingleHopCircuits':
        '1',
        'ExcludeSingleHopRelays':
        '0'
        #'FetchDirInfoEarly': '1',
        #'FetchDirInfoExtraEarly': '1',
    },
    init_msg_handler=success,
    completion_percent=100)

try:
    with stem.control.Controller.from_port(port=CONTROLLER_PORT) as controller:
        controller.authenticate()
        if not controller:
            failure(
                "Couldn't connect to Tor, controller.authenticate() failed")

        # Attaches a specific circuit to the given stream (event)
        def attach_stream(event):
            try:
                controller.attach_stream(event.id, circuit_id)
            except (OperationFailed, InvalidRequest), e:
                warning(
                    "Failed to attach stream to %s, unknown circuit. Closing stream..."
                    % circuit_id)
                print("\tResponse Code: %s " % str(e.code))
                print("\tMessage: %s" % str(e.message))
                controller.close_stream(event.id)

        # An event listener, called whenever StreamEvent status changes
        def probe_stream(event):
            if event.status == 'DETACHED':
                if circuit_id is not None:
                    warning("Stream Detached from circuit {0}...".format(
                        circuit_id))
                else:
                    warning("Stream Detached from circuit...")
                print("\t" + str(vars(event)))
            if event.status == 'NEW' and event.purpose == 'USER':
                attach_stream(event)

        controller.add_event_listener(probe_stream, EventType.STREAM)

        print(controller.get_info('circuit-status'))

        server = CorruptTorServer(TOR_SERVER_PORT, controller)
        server.start()
        server.join()
except Exception as e:
    print e
    tor_process.kill()
finally:
    tor_process.kill()
