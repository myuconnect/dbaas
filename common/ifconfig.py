from __future__ import print_function
import socket, json

import psutil
from psutil._common import bytes2human


af_map = {
    socket.AF_INET: 'IPv4',
    socket.AF_INET6: 'IPv6',
    psutil.AF_LINK: 'MAC',
}

duplex_map = {
    psutil.NIC_DUPLEX_FULL: "full",
    psutil.NIC_DUPLEX_HALF: "half",
    psutil.NIC_DUPLEX_UNKNOWN: "?",
}


def main():
    stats = psutil.net_if_stats()
    io_counters = psutil.net_io_counters(pernic=True)
    for nic, addrs in psutil.net_if_addrs().items():
        print("%s:" % (nic))
        if nic in stats:
            st = stats[nic]
            print("    stats          : ", end='')
            print("speed=%sMB, duplex=%s, mtu=%s, up=%s" % (
                st.speed, duplex_map[st.duplex], st.mtu,
                "yes" if st.isup else "no"))
        if nic in io_counters:
            io = io_counters[nic]
            print("    incoming       : ", end='')
            print("bytes=%s, pkts=%s, errs=%s, drops=%s" % (
                bytes2human(io.bytes_recv), io.packets_recv, io.errin,
                io.dropin))
            
            print("    outgoing       : ", end='')
            print("bytes=%s, pkts=%s, errs=%s, drops=%s" % (
                bytes2human(io.bytes_sent), io.packets_sent, io.errout,
                io.dropout))
        myAllNicAddress = []
        for addr in addrs:
            print("    %-4s" % af_map.get(addr.family, addr.family), end="")
            print(" address   : %s" % addr.address)
            if addr.broadcast:
                print("         broadcast : %s" % addr.broadcast)
            if addr.netmask:
                print("         netmask   : %s" % addr.netmask)
            if addr.ptp:
                print("      p2p       : %s" % addr.ptp)
        print("")

def nicStatsInJson():
    stats = psutil.net_if_stats()
    ioCounters = psutil.net_io_counters(pernic=True)
    myAllNicStats = []
    for nic, addrs in psutil.net_if_addrs().items():
        if nic in stats:
            st = stats[nic]
            myNicStats = {"speed" : st.speed, "duplex" : duplex_map[st.duplex], "mtu" : st.mtu, "up" : "yes" if st.isup else "no"}
        else:
            myNicStats = {}
        if nic in ioCounters:
            io = ioCounters[nic]        
            myNicIOCntrs = {
                "incoming" : {
                    "bytesRaw" : io.bytes_recv, 
                    "bytes" : bytes2human(io.bytes_recv), 
                    "packets" : io.packets_recv, 
                    "errs" : io.errin, 
                    "drops" : io.dropin
                }
            }
            myNicIOCntrs.update( {
                "outgoing" : {
                    "bytesRaw" : io.bytes_sent, 
                    "bytes" : bytes2human(io.bytes_sent), 
                    "packets" : io.packets_sent, 
                    "errs" : io.errout, 
                    "drops" : io.dropout
                }
            })
        myAllNicAddress = []
        for addr in addrs:
            myNicAddress = {"addressType" : af_map.get(addr.family, addr.family), "address" : addr.address}
            if addr.broadcast:
                myNicAddress.update({"broadcast" : addr.broadcast})
            if addr.netmask:
                myNicAddress.update({"netmask" : addr.netmask})
            if addr.ptp:
                myNicAddress.update({"p2p" : addr.ptp})
            myAllNicAddress.append(myNicAddress)
        myAllNicStats.append({nic : {"address" : myAllNicAddress, "stats" : myNicStats, "ioCounters" : myNicIOCntrs, "address" : myNicAddress}})

if __name__ == '__main__':
    main()
    nicStatsInJson()

