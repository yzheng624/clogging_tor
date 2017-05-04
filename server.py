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
        self.kill_received = False
        print 'Serving on port %s ...' % port

    def get_socket(self, ip, port):
        s = socks.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(CONNECTION_TIMEOUT)
        s.connect(ip, port)
        return s

class ClientServer(Server):
    def run(self):
        while True:
            try:
                client_connection, client_address = self.socket.accept()
                request = client_connection.recv(1024)
                now = datetime.utcnow()
                payload = request.decode()
                print '{} Client sent request.'.format(now)
                print payload
                if len(payload) == 0:
                    continue
                timestamp, microsecond = payload.split()
                timestamp = float(timestamp)
                past = datetime.utcfromtimestamp(int(timestamp)).replace(microsecond=int(microsecond))
                diff = now - past
                latency = diff.seconds * 1000000 + diff.microseconds
                queue.put(('Client', client_address[0], latency, timestamp))
                client_connection.close()
                if self.kill_received:
                    return
            except Exception as e:
                print e
                continue

class CorruptTorServer(Server):
    def run(self):
        while True:
            try:
                client_connection, client_address = self.socket.accept()
                request = client_connection.recv(1024)
                now = datetime.utcnow()
                payload = request.decode()
                print '{} Tor sent from {}.'.format(now, client_address)
                print payload
                timestamp, microsecond, name = payload.split()
                past = datetime.utcfromtimestamp(int(timestamp)).replace(microsecond=int(microsecond))
                diff = now - past
                latency = diff.seconds * 1000000 + diff.microseconds
                queue.put((name, client_address[0], latency, timestamp))
                client_connection.close()
                if self.kill_received:
                    return
            except Exception as e:
                print e
                continue

class ConsumerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.dataframe = pd.DataFrame(columns=['Client', 'Relay0', 'Relay1', 'Relay2', 'Relay3'])
        self.kill_received = False

    def run(self):
        count = 1
        while True:
            if not queue.empty():
                item = queue.get()
                name, client_address, latency, timestamp = item
                timestamp = int(timestamp) / 5
                if name == 'Client':
                    if timestamp in self.dataframe.index and not pd.isnan(self.dataframe.loc[timestamp, 'Client']):
                        self.dataframe.loc[timestamp, 'Client'] = (latency + self.dataframe.loc[timestamp, 'Client']) / 2
                    else:
                        self.dataframe.loc[timestamp, 'Client'] = latency
                else:
                    if timestamp in self.dataframe.index and not pd.isnan(self.dataframe.loc[timestamp, name]):
                        self.dataframe.loc[timestamp, name] = (latency + self.dataframe.loc[timestamp, name]) / 2
                    else:
                        self.dataframe.loc[timestamp, name] = latency
                count += 1
                print count
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
