#! /usr/bin/env python3

import argparse
import signal
import os
import pickle
import time

from datetime import datetime,timezone
from multiprocessing import Pipe
from multiprocessing.connection import wait

from pycoin.symbols.btc import network

COIN = 100_000_000

from watcher import Watcher
from extrapools import EXTRAPOOLS

POOLS = EXTRAPOOLS + [
    ["Luxor", "stratum+tcp://btc.global.luxor.tech:700", "test.worker1:pass"],
    ["ViaBTC", "stratum+tcp://btc.viabtc.com:3333", "achow101.001:123"],
    ["F2Pool", "stratum+tcp://btc-eu.f2pool.com:3333", "achow102.001:21235365876986800"],
    ["BTC.com", "stratum+tcp://eu.ss.btc.com:1800", "achow101eu.wentaproot:wentaproot"],
    ["Kano", "stratum+tcp://sg.kano.is:3333", "achow101.wentaproot:x"],
    ["Ckpool", "stratum+tcp://solo.ckpool.org:3333", "bc1qmuf9u75g745955f67c85nd33pdyh4v8zzr2lms.wentaproot:x"],
    ["Poolin", "stratum+tcp://btc.ss.poolin.me:443", "achow101.001:123"],
    ["SigmaPool", "stratum+tcp://eu1.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    ["Binance", "stratum+tcp://bs.poolbinance.com:3333", "achow101.wentaproot:x"],
    ["EMCD", "stratum+tcp://gate.emcd.io:3333", "achow101.wentaproot:x"],
    ["Rawpool", "stratum+tcp://ru.ss.rawpool.com:1800", "miner1.wentaproot:x"],
    ["SecPool", "stratum+tcp://btc.secpool.com:3333", "miner1.wentaproot:x"],
    # ["Foundry", "stratum+tcp://btc.foundryusapool.com:3333", "miner1.wentaproot:x"],
    ["Ultimus", "stratum+tcp://bs.ultimuspool.com:8888", "miner1.wentaproot:x"],
]

parser = argparse.ArgumentParser(
    description="Run the watcher.py script for multiple hardcoded pools"
)
parser.add_argument("--debug")
args = parser.parse_args()

state = dict()
watchers = dict()

def colorize(data, text=None):
    if text == None:
        text = data
    reset = "\033[0m"
    h = hash(data)
    hh = hash(h)
    foreground = f"\u001b[48;5;{21+ h%210}m" #f"\033[0;32m"
    background = f"\u001b[38;5;0m" #f"\033[0;32m"
    return f"{foreground}{background}{text}{reset}"

def gradient(a):
    colors = [46, 82, 76, 112, 106, 142, 136, 172, 166, 202, 160, 196]

def print_state():
    text = "\n\n"
    text += "  " + datetime.now().strftime('%H:%M:%S') + "\n"
    # text += f"  {'pool name': <18}  {'height'}  {'building on block':<66} {'txns':<5} {'block template':<24}   {'job'}    {'reward (sorted)':<14} {'name':>18}\n"
    text += f"  {'pool name': <18} {'height'}   {'txns':<5} {'block template':<104}   {'job'}    {'reward (sorted)':<14} {'clear jobs'} {'name':>12}\n"
    for name in sorted(state, reverse=True, key=lambda name: str(state[name]["height"])+state[name]["prev"]+str(state[name]["coinbase_out"])):
        text += f"  {name: <18}"
        text += f" {colorize(' '+ str(state[name]['height']) + ' ')}"
        # text += f" {colorize(' ' + state[name]['prev'] + ' ')}"
        text += f" {'empty' if len(state[name]['branches']) == 0 else '>'+ str(2**(len(state[name]['branches'])-1 )):<5}"
        text += f" {''.join([colorize(branch, ' ' + branch[:6] + ' ') for branch in state[name]['branches']]):<104}"
        text += f" {int(datetime.now(timezone.utc).timestamp() - state[name]['timestamp']):>3}s ago"
        #text += f" {int(datetime.now(timezone.utc).timestamp() - state[name]['conn_time']):>4}s ago"
        text += f" {state[name]['coinbase_out'] / COIN:<10} BTC"
        text += f" {'true' if state[name]['clear_jobs'] == 1 else 'false':>6}"
        text += f"  {name:>16}"
        text += "\n"
    #os.system('clear')
    print(text)

def start_watcher(pool):
    send, recv = Pipe()
    process = Watcher(pool[0], pool[1], pool[2], send, name=f"Watcher {pool[0]}")
    process.start()
    watchers[pool[0]] = {
        "process": process,
        "receiver": recv,
        "pool": pool,
    }
    send.close()


# Start all watcher processes
if __name__ == '__main__':
    for pool in POOLS:
        start_watcher(pool)    

    with open(f"stratum-watcher-{int(datetime.now(timezone.utc).timestamp())}.pickle", 'ab+') as fp:
        while True:
            print_state()
            for r in wait([watchers[name]["receiver"] for name in watchers], timeout=1):    
                msg = r.recv()
                poolname = msg['name']
                if "close" in msg:
                    watchers[poolname]["process"].terminate()
                    start_watcher(watchers[poolname]["pool"])
                else:
                    state[poolname] = msg
                    pickle.dump(msg, fp)
