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
    # ["stratum+tcp://btc.luxor.tech:700", "test.wentaproot:x"],
    ["ViaBTC", "stratum+tcp://btc.viabtc.com:3333", "achow101.001:123"],
    # ["stratum+tcp://btc.f2pool.com:3333", "achow102.001:21235365876986800"],
    # ["stratum+tcp://btc-na.f2pool.com:3333", "achow102.001:21235365876986800"],
    ["F2Pool", "stratum+tcp://btc-eu.f2pool.com:3333", "achow102.001:21235365876986800"],
    # ["stratum+tcp://us.ss.btc.com:1800", "achow101.wentaproot:wentaproot"],
    ["BTC.com", "stratum+tcp://eu.ss.btc.com:1800", "achow101eu.wentaproot:wentaproot"],
    #["stratum+tcp://ss.antpool.com:3333", "achow101.wentaproot:wentaproot"],
    # ["stratum+tcp://stratum.kano.is:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://or.kano.is:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://nya.kano.is:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://nl.kano.is:3333", "achow101.wentaproot:x"],
    ["Kano", "stratum+tcp://sg.kano.is:3333", "achow101.wentaproot:x"],
    ["Ckpool", "stratum+tcp://solo.ckpool.org:3333", "bc1qmuf9u75g745955f67c85nd33pdyh4v8zzr2lms.wentaproot:x"],
    # ["stratum+tcp://btc.ss.poolin.com:443", "achow101.001:123"],
    # ["stratum+tcp://btc-bj.ss.poolin.com:443", "achow101.001:123"],
    # ["stratum+tcp://btc-cd.ss.poolin.com:443", "achow101.001:123"],
    # ["stratum+tcp://btc-va.ss.poolin.com:443", "achow101.001:123"],
    ["Poolin", "stratum+tcp://btc.ss.poolin.me:443", "achow101.001:123"],
    # ["stratum+tcp://ru1.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://ru2.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://ru3.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://us1.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://us2.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    ["SigmaPool", "stratum+tcp://eu1.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://eu2.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://eu3.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://cn1.btc.sigmapool.com:3333", "achow101.wentaproot:x"],
    ["Binance", "stratum+tcp://bs.poolbinance.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://bs.poolbinance.com:443", "achow101.wentaproot:x"],
    # ["stratum+tcp://bs.poolbinance.com:8888", "achow101.wentaproot:x"],
    # ["stratum+tcp://bs.poolbinance.com:1800", "achow101.wentaproot:x"],
    # ["stratum+tcp://sha256.poolbinance.com:8888", "achow101.wentaproot:x"],
    # ["stratum+tcp://sha256.poolbinance.com:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://sha256.poolbinance.com:1800", "achow101.wentaproot:x"],
    # ["stratum+tcp://sha256.poolbinance.com:443", "achow101.wentaproot:x"],
    ["EMCD", "stratum+tcp://gate.emcd.io:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://eu.emcd.io:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://cn.emcd.io:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://us.emcd.io:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://ir.emcd.io:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://kz.emcd.io:3333", "achow101.wentaproot:x"],
    # ["stratum+tcp://ru.ss.rawpool.com:443", "miner1.wentaproot:x"],
    ["Rawpool", "stratum+tcp://ru.ss.rawpool.com:1800", "miner1.wentaproot:x"],
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
    text = "\n\n\n"
    text += f"  {'pool name': <18}  {'height'}  {'building on block':<66} {'txns':<5} {'block template':<24}   {'job'}    {'reward (sorted)':<14} {'name':>18}\n"
    for name in sorted(state, reverse=True, key=lambda name: str(state[name]["height"])+state[name]["prev"]+str(state[name]["coinbase_out"])):
        text += f"  {name: <18}"
        text += f" {colorize(' '+ str(state[name]['height']) + ' ')}"
        text += f" {colorize(' ' + state[name]['prev'] + ' ')}"
        text += f" {'empty' if len(state[name]['branches']) == 0 else '>'+ str(2**(len(state[name]['branches'])-1 )):<5}"
        text += f" {''.join([colorize(branch, '  ') for branch in state[name]['branches']]):>24}"
        text += f" {int(datetime.now(timezone.utc).timestamp() - state[name]['timestamp']):>3}s ago"
        #text += f" {int(datetime.now(timezone.utc).timestamp() - state[name]['conn_time']):>4}s ago"
        text += f" {state[name]['coinbase_out'] / COIN:<10} BTC"
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
