import socket
import time
import pandas as pd
from datetime import datetime
import threading
import Queue
from settings import *

HOST, PORT = '', 8000

BUF_SIZE = 1000
queue = Queue.Queue(BUF_SIZE)

class Server(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((HOST, int(port)))
        self.socket.listen(1)
        print 'Serving on port %s ...' % port

    def get_socket(self, ip, port):
        s = socks.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(CONNECTION_TIMEOUT)
        s.connect(ip, port)
        return s

class ClientServer(Server):
    def run(self):
        while True:
            client_connection, client_address = self.socket.accept()
            request = client_connection.recv(1024)
            now = datetime.utcnow()
            payload = request.decode()
            print '{} Client sent request.'.format(now)
            print payload
            timestamp, microsecond = payload.split()
            past = datetime.utcfromtimestamp(int(timestamp)).replace(microsecond=int(microsecond))
            diff = now - past
            latency = diff.second * 1000 + diff.microsecond
            queue.put(('Client', client_address, latency, timestamp))
            client_connection.close()
            if self.kill_received:
                return

class CorruptTorServer(Server):
    def run(self):
        while True:
            client_connection, client_address = self.socket.accept()
            request = client_connection.recv(1024)
            now = datetime.utcnow()
            payload = request.decode()
            print '{} Tor sent from {}.'.format(now, client_address)
            print payload
            timestamp, microsecond = payload.split()
            past = datetime.utcfromtimestamp(int(timestamp)).replace(microsecond=int(microsecond))
            diff = now - past
            latency = diff.second * 1000 + diff.microsecond
            queue.put(('Tor', client_address, latency, timestamp))
            client_connection.close()
            if self.kill_received:
                return

class ConsumerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.dataframe = pd.DataFrame(columns=['Client', 'Relay0', 'Relay1', 'Relay2', 'Relay3'])

    def run(self):
        count = 0
        while True:
            if not queue.empty():
                item = queue.get()
                name, client_address, latency, timestamp = item
                if name == 'Client':
                    self.dataframe.loc[timestamp / 10, 'Client'] = latency
                else:
                    self.dataframe.loc[timestamp / 10, IP_TO_NAME[client_address]] = latency
                count += 1
            if count % 1000 == 0:
                print self.dataframe.head()
                self.dataframe.to_csv('out.csv')
                count = 0
            if self.kill_received:
                return

def main():
    threads = []
    threads.append(ClientServer(SERVER_TO_CLIENT_PORT))
    threads.append(CorruptTorServer(SERVER_TO_TOR_PORT))
    threads.append(ConsumerThread())
    for thread in threads:
        thread.start()
    while len(threads) > 0:
        try:
            # Join all threads using a timeout so it doesn't block
            # Filter out threads which have been joined or are None
            threads = [t.join(1000) for t in threads if t is not None and t.isAlive()]
        except KeyboardInterrupt:
            print "Ctrl-c received! Sending kill to threads..."
            for t in threads:
                t.kill_received = True

if __name__ == '__main__':
    main()
