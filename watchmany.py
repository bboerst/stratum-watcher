#! /usr/bin/env python3

import argparse
import signal

from watcher import Watcher

POOLS = [
    ["stratum+tcp://bs.poolbinance.com:1800", "achow101.wentaproot:x"],
    ["stratum+tcp://sha256.poolbinance.com:1800", "achow101.wentaproot:x"],
]

parser = argparse.ArgumentParser(
    description="Run the watcher.py script for multiple hardcoded pools"
)
parser.add_argument("--debug")
parser.add_argument(
    "--rpccookiefile",
    help="Cookie file for Bitcoin Core RPC creds",
    default="~/.bitcoin/.cookie",
)
args = parser.parse_args()

procs = []

# Handler for SIGINT that stops all of the processes
def sigint_handler(signal, frame):
    global procs
    for p in procs:
        p.close()
        p.terminate()


# Start all watcher processes
signal.signal(signal.SIGINT, signal.SIG_IGN)
for pool in POOLS:
    proc = Watcher(pool[0], pool[1], args.rpccookiefile, name=f"Watcher {pool[0]}")
    proc.start()
    procs.append(proc)

signal.signal(signal.SIGINT, sigint_handler)

# Interrupt and wait for all of the processes to end
for p in procs:
    p.join()
