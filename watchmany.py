#! /usr/bin/env python3

import argparse
import signal
import os
import pickle
import time
from datetime import datetime,timezone
from multiprocessing import Pipe
from multiprocessing.connection import wait

from watcher import Watcher
from extrapools import EXTRAPOOLS

POOLS = EXTRAPOOLS + [
    ["Luxor", "stratum+tcp://btc.global.luxor.tech:700", "test.worker1:pass"],
    # ["stratum+tcp://btc.luxor.tech:700", "test.wentaproot:x"],
    ["ViaBTC", "stratum+tcp://btc.viabtc.com:3333", "achow101.001:123"],
    # ["stratum+tcp://btc.f2pool.com:3333", "achow102.001:21235365876986800"],
    # ["stratum+tcp://btc-na.f2pool.com:3333", "achow102.001:21235365876986800"],
    ["F2Pool", "stratum+tcp://btc-eu.f2pool.com:3333", "achow102.001:21235365876986800"],
    # ["stratum+tcp://us.ss.btc.com:1800", "achow101.wentaproot:wentaproot"],
    ["+ BTC.com", "stratum+tcp://eu.ss.btc.com:1800", "achow101eu.wentaproot:wentaproot"],
    #["stratum+tcp://ss.antpool.com:3333", "achow101.wentaproot:wentaproot"],
    # ["stratum+tcp://stratum.kano.is:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://or.kano.is:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://nya.kano.is:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://nl.kano.is:3333", "achow101.wentaproot:x"],
    ["Kano", "stratum+tcp://sg.kano.is:3333", "achow101.wentaproot:x"],
    ["ckpool", "stratum+tcp://solo.ckpool.org:3333", "bc1qmuf9u75g745955f67c85nd33pdyh4v8zzr2lms.wentaproot:x"],
    # ["stratum+tcp://btc.ss.poolin.com:443", "achow101.001:123"],
    # ["stratum+tcp://btc-bj.ss.poolin.com:443", "achow101.001:123"],
    # ["stratum+tcp://btc-cd.ss.poolin.com:443", "achow101.001:123"],
    # ["stratum+tcp://btc-va.ss.poolin.com:443", "achow101.001:123"],
    ["+ Poolin", "stratum+tcp://btc.ss.poolin.me:443", "achow101.001:123"],
    # ["stratum+tcp://ru1.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://ru2.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://ru3.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://us1.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://us2.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    ["SigmaPool", "stratum+tcp://eu1.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://eu2.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://eu3.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://cn1.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    ["+ Binance", "stratum+tcp://bs.poolbinance.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://bs.poolbinance.com:443", "achow101.wentaproot:x"],
    # ["stratum+tcp://bs.poolbinance.com:8888", "achow101.wentaproot:x"],
    # ["stratum+tcp://bs.poolbinance.com:1800", "achow101.wentaproot:x"],
    # ["stratum+tcp://sha256.poolbinance.com:8888", "achow101.wentaproot:x"],
    # ["stratum+tcp://sha256.poolbinance.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://sha256.poolbinance.com:1800", "achow101.wentaproot:x"],
    # ["stratum+tcp://sha256.poolbinance.com:443", "achow101.wentaproot:x"],
    ["+ emcd", "stratum+tcp://gate.emcd.io:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://eu.emcd.io:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://cn.emcd.io:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://us.emcd.io:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://ir.emcd.io:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://kz.emcd.io:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://ru.ss.rawpool.com:443", "miner1.wentaproot:x"],
    ["+ Rawpool", "stratum+tcp://ru.ss.rawpool.com:1800", "miner1.wentaproot:x"],
    ["SecPool", "stratum+tcp://btc.secpool.com:3333", "miner1.wentaproot:x"],
    ["Foundry", "stratum+tcp://btc.foundryusapool.com:3333", "miner1.wentaproot:x"],
    ["Ultimus", "stratum+tcp://bs.ultimuspool.com:8888", "miner1.wentaproot:x"],


    # Down?
    # ["stratum+tcp://stratum.1thash.btc.top:8888", "achow102.wentaproot:wentaproot"],
    # ["stratum+tcp://bak.1thash.btc.top:3333", "achow102.wentaproot:wentaproot"],
    # ["stratum+tcp://cn.ss.btc.com:1800", "achow101cn.wentaproot:wentaproot"],
    # ["stratum+tcp://sz.ss.btc.com:1800", "achow101sz.wentaproot:wentaproot"],
    # ["stratum+tcp://stratum.btc.top:8888", "achow101.001:123"],
    # ["stratum+tcp://bak.btc.top:3333", "achow101.001:123"],
    # ["stratum+tcp://btc-us.luxor.tech:6000", "achow101.wentaproot:x"],
    # ["stratum+tcp://btc-asia.luxor.tech:6000", "achow101.wentaproot:x"],
    # ["stratum+tcp://btc-eu.luxor.tech:6000", "achow101.wentaproot:x"],
    # ["stratum+tcp://bn.huobipool.com:1800", "achow101.wentaproot:x"],
    # ["stratum+tcp://bn.huobipool.com:443", "achow101.wentaproot:x"],
    # ["stratum+tcp://bn.huobipool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://bs.huobipool.com:1800", "achow101.wentaproot:x"],
    # ["stratum+tcp://bs.huobipool.com:443", "achow101.wentaproot:x"],
    # ["stratum+tcp://bs.huobipool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://stratum.poolhb.com:8888", "achow101.wentaproot:x"],
    # ["stratum+tcp://stratum.poolhb.com:7777", "achow101.wentaproot:x"],
    # ["stratum+tcp://stratum.poolhb.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://hb.ss.rawpool.com:443", "miner1.wentaproot:x"],
    # ["stratum+tcp://hb.ss.rawpool.com:1800", "miner1.wentaproot:x"],
    # ["stratum+tcp://hn.ss.rawpool.com:443", "miner1.wentaproot:x"],
    # ["stratum+tcp://hn.ss.rawpool.com:1800", "miner1.wentaproot:x"],

    # Some send empty msgs, no jobs
    # ["stratum+tcp://bm.huobipool.com:1800", "achow101.wentaproot:x"],
    # ["stratum+tcp://bm.huobipool.com:443", "achow101.wentaproot:x"],
    # ["stratum+tcp://bm.huobipool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://bu.huobipool.com:1800", "achow101.wentaproot:x"],
    # ["stratum+tcp://bu.huobipool.com:443", "achow101.wentaproot:x"],
    # ["stratum+tcp://bu.huobipool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://hk.huobipool.com:8888", "achow101.wentaproot:x"],
    # ["stratum+tcp://hk.huobipool.com:7777", "achow101.wentaproot:x"],
    # ["stratum+tcp://hk.huobipool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://us.ss.rawpool.com:443", "miner1.wentaproot:x"],
    # ["stratum+tcp://us.ss.rawpool.com:1800", "miner1.wentaproot:x"],
    # ["stratum+tcp://eu.ss.rawpool.com:443", "miner1.wentaproot:x"],
    # ["stratum+tcp://eu.ss.rawpool.com:1800", "miner1.wentaproot:x"],

    # Sends garbage?
    # ["stratum+tcp://eu.stratum.slushpool.com:3333", "achow101.worker1:pass"],
    # ["stratum+tcp://us-east.stratum.slushpool.com:3333", "achow101.worker1:pass"],
    # ["stratum+tcp://ca.stratum.slushpool.com:3333", "achow101.worker1:pass"],
    # ["stratum+tcp://sg.stratum.slushpool.com:3333", "achow101.worker1:pass"],
    # ["stratum+tcp://jp.stratum.slushpool.com:3333", "achow101.worker1:pass"],
    # ["stratum+tcp://ru-west.stratum.slushpool.com:3333", "achow101.worker1:pass"],
    
]

parser = argparse.ArgumentParser(
    description="Run the watcher.py script for multiple hardcoded pools"
)
parser.add_argument("--debug")
args = parser.parse_args()

state = dict()
procs = []
receivers = list()


def colorize(data):
    reset = "\033[0m"
    h = hash(data)
    hh = hash(h)
    foreground = f"\u001b[48;5;{1+ h%231}m" #f"\033[0;32m"
    background = f"\u001b[38;5;0m" #f"\033[0;32m"
    return f"{foreground}{background} {data} {reset}"
    

def print_state():
    text = "\n\n\n"
    def branch(x):
        return f"{' branch ' + str(x):<10}"
    max_branches = max([len(state[pool]["branches"]) for pool in state])
    
    text += f"  {'pool name': <18} {'tx after coinbase/branch 0':<64}  {' '.join(branch(n+1) for n in range(max_branches-1))} \n" 
    
    for name in sorted(state, key=lambda name: state[name]["branches"]):
        short_branches = [colorize(l[:8]) for l in state[name]["branches"]]
        text += f"  {name: <18} {colorize(state[name]['first_tx'])} {' '.join(short_branches[1:])} {int(datetime.now(timezone.utc).timestamp() - state[name]['timestamp'])}s ago\n"
    os.system('clear')
    print(text)

# Handler for SIGINT that stops all of the processes
def sigint_handler(signal, frame):
    global procs
    for p in procs:
        p.close()
        p.terminate()


# Start all watcher processes
for pool in POOLS:
    send, recv = Pipe()
    receivers.append(recv)    
    proc = Watcher(pool[0], pool[1], pool[2], send, name=f"Watcher {pool[0]}")
    proc.start()
    procs.append(proc)    

with open(f"stratum-watcher{datetime.now(timezone.utc).timestamp()}.pickle", 'ab+') as fp:
    while receivers:
        for r in wait(receivers, timeout=0.5):
            try:
                msg = r.recv()
            except EOFError:
                receivers.remove(r)
            else:
                state[msg["name"]] = msg
                pickle.dump(msg, fp)
                print_state()

# Interrupt and wait for all of the processes to end
for p in procs:
    p.join()
