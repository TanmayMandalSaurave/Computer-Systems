#!/usr/bin/env python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.node import CPULimitedHost, Host, Node
from mininet.link import TCLink, Intf
import argparse
import threading
import time

class NetworkTopo( Topo ):
    "Topology for question 2"

    # pylint: disable=arguments-differ
    def build( self, **_opts ):

        s1, s2 = [ self.addSwitch( s ) for s in ( 's1', 's2' ) ]

        h1 = self.addHost( 'h1', cls=Host, ip = '10.0.0.1/24', defaultRoute=None)
        h2 = self.addHost( 'h2', cls=Host, ip = '10.0.0.2/24', defaultRoute=None)
        h3 = self.addHost( 'h3', cls=Host, ip = '10.0.0.3/24', defaultRoute=None)
        h4 = self.addHost( 'h4', cls=Host, ip = '10.0.0.4/24', defaultRoute=None)
        
        self.addLink(h1,s1,cls=TCLink, **{'bw':2,'delay':2})
        self.addLink(h2,s1,cls=TCLink, **{'bw':2,'delay':2})
        self.addLink(h3,s2,cls=TCLink, **{'bw':2,'delay':2})
        self.addLink(h4,s2,cls=TCLink, **{'bw':2,'delay':2})
        self.addLink(s1,s2,cls=TCLink, **{'bw':8,'delay':2,'loss': args.loss})
        
def run(args):
    "Test the topology"
    topo = NetworkTopo()
    net = Mininet( topo=topo, waitConnected=True )  # controller is used by switches
    
    net.start()
    h1, h2, h3, h4, s1, s2 = net.get('h1', 'h2', 'h3', 'h4', 's1', 's2')
    s1_pcap = net['s1'].popen('tcpdump -i any -w s1_dump.pcap')
    s1.cmd('tcpdump -i any -w output.pcap &') 

    if args.config == 'b':
        h4.cmd('iperf -s &')
        time.sleep(1)
        print(h1.cmd(f'iperf -c {h4.IP()} -Z {args.cc}'))
    elif args.config == 'c':
        h4.cmd('iperf -s &')
        time.sleep(2)
	# Run the hosts simultaneously
        print('Running hosts simultaneously')
        threads = []
        for h in [h1, h2, h3]:
            t = threading.Thread(target=measure_throughput_and_latency, args=(h, h4, {args.cc}))
            t.start()
            threads.append(t)

        # Wait for all threads to finish
        for t in threads:
            t.join()
    CLI(net)

    h4.cmd('pkill -SIGINT iperf')
    s1_pcap.terminate()
    net.stop()

def measure_throughput_and_latency(h, h4, scheme):
    #print('Iperf throughput from %s to H4 with %s:' % (h.name, scheme))
    iperf_output = h.cmd('iperf -c %s -t 10' % h4.IP())
    print('Iperf throughput from %s to H4 with %s:\n' % (h.name, scheme),iperf_output)


    #print('Ping latency from %s to H4 with %s:' % (h.name, scheme))
    ping_output = h.cmd('ping -c 4 %s' % h4.IP())
    print('Ping latency from %s to H4 with %s:\n' % (h.name, scheme),ping_output)


if __name__ == '__main__':
    setLogLevel( 'info' )
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--config',type=str,choices=['b','c'],required=True)
    arg_parser.add_argument('--loss',type=int,default=0)
    arg_parser.add_argument('--cc',type=str,choices=['vegas','reno','cubic','bbr'],required=True)
    args = arg_parser.parse_args()
    run(args)