import StringIO
import time
import argparse
import sys
from datetime import datetime
import socket

import stem.control
from stem.util import term
import stem.process
from stem.control import EventType
from stem import CircStatus, OperationFailed, InvalidRequest, InvalidArguments, CircuitExtensionFailed

from settings import *

SOCKS_PORT = 7000
CONTROLLER_PORT = 9051
CONNECTION_TIMEOUT = 30  # timeout before we give up on a circuit

parser = argparse.ArgumentParser(
    prog='client',
    description="Measure latency between either a pair of Tor relays (relay1,relay2), or a list of pairs, specified with the --input-file argument."
)
parser.add_argument('relay1', help="First relay", nargs='?', default='7B3F666CD6665CFF146F61CE005DD19F89DBC23A')
parser.add_argument('relay2', help="Second relay", nargs='?', default='15999A15088C133AF85AAF73DB74AC5C7B28114D')
parser.add_argument('relay3', help="Thrid relay", nargs='?', default='7FBD5CCE31EAC5CED96F88ACA9D69656DA75CDF7')
args = vars(parser.parse_args())
path = [args['relay1'], args['relay2'], args['relay3']]

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
        #'FetchDirInfoEarly': '1',
        #'FetchDirInfoExtraEarly': '1',
    },
    init_msg_handler=success,
    completion_percent=80)

circuit_id = None
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
                    warning("Stream Detached from circuit {0}...".format(circuit_id))
                else:
                    warning("Stream Detached from circuit...")
                print("\t" + str(vars(event)))
            if event.status == 'NEW' and event.purpose == 'USER':
                attach_stream(event)

        controller.add_event_listener(probe_stream, EventType.STREAM)

        print(controller.get_info('circuit-status'))

        circuit_id = controller.new_circuit(path=path, await_build=True)
        print circuit_id

        print(controller.get_info('circuit-status'))
        socks.setdefaultproxy(SOCKS_TYPE, SOCKS_HOST, SOCKS_PORT)
        socket.socket = socks.socksocket

        while True:
            print '%0.5f' % time.time()
            s = socks.socksocket()
            s.settimeout(CONNECTION_TIMEOUT)
            s.connect((SERVER_ADDRESS, SERVER_TO_CLIENT_PORT))
            now = datetime.now()
            timestamp = time.mktime(now.timetuple())
            data = '{} {}'.format(timestamp, now.microsecond)
            print data
            s.send(data)
            s.close()
            time.sleep(1)
except Exception as e:
    print e
    tor_process.kill()
finally:
    tor_process.kill()
