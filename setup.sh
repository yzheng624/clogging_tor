sudo apt-get update
sudo apt-get install tor -y

cat <<EOT >> torrec
TestingTorNetwork 1
RunAsDaemon 0
Nickname CorruptTor
ShutdownWaitLength 0
ProtocolWarnings 1
SafeLogging 0
DisableDebuggerAttachment 0
DirAuthority auth orport=5000 no-v2 v3ident=A9495BBC01F3B30247673A7C3253EDF21687468E 54.197.200.127:7000 584C 788B 916E 8C3D 12F1 F750 9199 9038 09A5 1CF7

SocksPort 0
ControlPort 9051
OrPort 5000
AllowSingleHopExits 1

# An exit policy that allows exiting to IPv4 LAN
ExitPolicy accept 0.0.0.0/32:*

ContactInfo your@contact.info
EOT

sudo apt-get install python python-pip
pip install pandas
pip install stem

tor --list-fingerprint -f torrec
tor -f torrec

sudo apt-get install libevent-dev libssl-dev
wget -c https://www.torproject.org/dist/tor-0.3.0.6.tar.gz
tar zxvf tor-0.3.0.6.tar.gz
# modify or/or.h based on
# https://tor.stackexchange.com/questions/1312/how-to-decrease-number-of-tor-hops/1662
# https://github.com/aagbsn/torflow/blob/master/tordiffs/one-hop.diff
./configure
