#!/usr/bin/env python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI


class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    # pylint: disable=arguments-differ
    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()


class NetworkTopo( Topo ):
    "Topology for question 1"

    # pylint: disable=arguments-differ
    def build( self, **_opts ):
        
        router_ra_device_ip = '192.168.1.1/24'
        router_rb_device_ip = '192.168.2.1/24'
        router_rc_device_ip = '192.168.3.1/24'
        host_route_1 = 'via 192.168.1.1'
        host_route_2 = 'via 192.168.2.1'
        host_route_3 = 'via 192.168.3.1'

        ra = self.addNode( 'ra', cls=LinuxRouter, ip=router_ra_device_ip )
        rb = self.addNode( 'rb', cls=LinuxRouter, ip=router_rb_device_ip )
        rc = self.addNode( 'rc', cls=LinuxRouter, ip=router_rc_device_ip )

        s1, s2, s3, s4 = [ self.addSwitch( s ) for s in ( 's1', 's2', 's3', 's4' ) ]
        
        self.addLink( s1, ra, intfName2='ra-eth1', params2={ 'ip' : router_ra_device_ip } )
        self.addLink( s2, rb, intfName2='rb-eth1', params2={ 'ip' : router_rb_device_ip } )
        self.addLink( s3, rc, intfName2='rc-eth1', params2={ 'ip' : router_rc_device_ip } )
        
        self.addLink( s4, ra, intfName2='ra-eth2', params2={ 'ip' : '192.168.4.1/24' } )
        self.addLink( s4, rb, intfName2='rb-eth2', params2={ 'ip' : '192.168.4.2/24' } )
        self.addLink( s4, rc, intfName2='rc-eth2', params2={ 'ip' : '192.168.4.3/24' } )
        
        h1 = self.addHost( 'h1', ip = '192.168.1.100/24', defaultRoute=host_route_1 )
        h2 = self.addHost( 'h2', ip = '192.168.1.101/24', defaultRoute=host_route_1 )
        h3 = self.addHost( 'h3', ip = '192.168.2.100/24', defaultRoute=host_route_2 )
        h4 = self.addHost( 'h4', ip = '192.168.2.101/24', defaultRoute=host_route_2 )
        h5 = self.addHost( 'h5', ip = '192.168.3.100/24', defaultRoute=host_route_3 )
        h6 = self.addHost( 'h6', ip = '192.168.3.101/24', defaultRoute=host_route_3 )
        
        self.addLink(h1,s1)
        self.addLink(h2,s1)
        self.addLink(h3,s2)
        self.addLink(h4,s2)
        self.addLink(h5,s3)
        self.addLink(h6,s3)
        
def run():
    "Test the topology"
    topo = NetworkTopo()
    net = Mininet( topo=topo, waitConnected=True )  # controller is used by switches
    
    # Add routing for reaching networks that aren't directly connected
    info(net['ra'].cmd("ip route add 192.168.2.0/24 via 192.168.4.2 dev ra-eth2"))
    info(net['ra'].cmd("ip route add 192.168.3.0/24 via 192.168.4.3 dev ra-eth2"))
    info(net['rb'].cmd("ip route add 192.168.1.0/24 via 192.168.4.1 dev rb-eth2"))
    info(net['rb'].cmd("ip route add 192.168.3.0/24 via 192.168.4.3 dev rb-eth2"))
    info(net['rc'].cmd("ip route add 192.168.1.0/24 via 192.168.4.1 dev rc-eth2"))
    info(net['rc'].cmd("ip route add 192.168.2.0/24 via 192.168.4.2 dev rc-eth2"))
    
    net.start()
    # info( '*** Routing Table on Router:\n' )
    # info( net[ 'ra' ].cmd( 'route' ) )
    ra_pcap = net['ra'].popen('tcpdump -i any -w ra_dump.pcap')
    rb_pcap = net['rb'].popen('tcpdump -i any -w rb_dump.pcap')
    rc_pcap = net['rc'].popen('tcpdump -i any -w rc_dump.pcap')
    CLI( net )
    ra_pcap.terminate()
    rb_pcap.terminate()
    rc_pcap.terminate()
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    run()