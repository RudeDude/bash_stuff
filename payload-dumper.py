#!/usr/bin/python3

# Written by Don J. Rude, 2024-09-09

from scapy.all import *
import argparse

print("Be sure you have pre-filtered your PCAP! You'll be dumping ALL raw packet payloads in PCAP order.")

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', default="my.pcap",
                    help='PCAP file to input (default: my.pcap)')
parser.add_argument('-o', '--output', default="out.bin",
                    help='File to dump all payload bytes (default: out.bin)')
args = parser.parse_args()

pcap = rdpcap(args.input)
out = open(args.output, "wb")

pcnt=0
wcnt=0
for pkt in pcap:
    pcnt += 1
    if Raw in pkt:
        wcnt += 1
        out.write(pkt[Raw].load)
print("Packets:", pcnt, "Written:", wcnt, "Percent:", (wcnt/pcnt*100), "%")

