#! /usr/bin/env python3

import argparse
import atexit
import json
import logging
import os
import socket
import struct
import sys
import time

from authproxy import AuthServiceProxy, JSONRPCException
from multiprocessing import Process
from urllib.parse import urlparse, urlunparse

from pycoin.symbols.btc import network

# Setup logging
file_handler = logging.FileHandler(filename="stratum-watcher.log")
stdout_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(
    handlers=[file_handler, stdout_handler],
    format="%(asctime)s %(levelname)s: %(message)s",
)
LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


class Watcher(Process):
    def __init__(self, poolname, url, userpass, pipe_send, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buf = b""
        self.id = 1
        self.poolname = poolname
        self.userpass = userpass
        self.extranonce1 = None
        self.extranonce2_length = -1
        self.last_log_time = time.time()
        self.socket_open_time = None
        self.pipe_send = pipe_send
        # Parse the URL
        self.purl = urlparse(url)
        if self.purl.scheme != "stratum+tcp":
            raise ValueError(
                f"Unrecognized scheme {self.purl.scheme}, only 'stratum+tcp' is allowed"
            )
        if self.purl.hostname is None:
            raise ValueError(f"No hostname provided")
        if self.purl.port is None:
            raise ValueError(f"No port provided")
        if self.purl.path != "":
            raise ValueError(f"URL has a path {self.purl.path}, this is not valid")

        self.init_socket()

    def init_socket(self):
        # Make the socket
        self.sock = socket.socket()
        self.sock.settimeout(600)
        self.socket_open_time = time.time()

    def close(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()
        LOG.info(f"Disconnected from {urlunparse(self.purl)}")
        self.pipe_send.send({"name": self.poolname, "close": True})

    def get_msg(self):
        while True:
            split_buf = self.buf.split(b"\n", maxsplit=1)
            r = split_buf[0]
            try:
                resp = json.loads(r)
                # Remove r from the buffer
                if len(split_buf) == 2:
                    self.buf = split_buf[1]
                else:
                    self.buf = b""

                # Decoded, so return this message
                return resp
            except (json.decoder.JSONDecodeError, ConnectionResetError):
                # Failed to decode, maybe missing, so try to get more
                new_buf = b""
                try:
                    new_buf = self.sock.recv(4096)
                except:
                    self.close()
                    raise EOFError
                if len(new_buf) == 0:
                    self.close()
                self.buf += new_buf

    def send_jsonrpc(self, method, params):
        # Build the jsonrpc request
        data = {
            #"jsonrpc": "2.0",
            "id": self.id,
            "method": method,
            "params": params,
        }
        self.id += 1

        # Send the jsonrpc request
        LOG.debug(f"Sending: {data}")
        json_data = json.dumps(data) + "\n"
        self.sock.send(json_data.encode())

        # Get the jsonrpc reqponse
        resp = self.get_msg()
        if "id" in resp and resp["id"] == 1 and "result" in resp:
            self.extranonce1, self.extranonce2_length = resp["result"][-2:]
        LOG.debug(f"Received: {resp}")

    def get_stratum_work(self):
        # Open TCP connection to the server
        self.sock.connect((self.purl.hostname, self.purl.port))
        LOG.debug(f"Connected to server {urlunparse(self.purl)}")

        # Subscribe to mining notifications
        self.send_jsonrpc("mining.subscribe", [])
        LOG.debug(f"{self.poolname}: Subscribed to pool notifications")

        # Authorize with the pool
        self.send_jsonrpc("mining.authorize", self.userpass.split(":"))
        LOG.debug(f"{self.poolname}: Authed with the pool")

        # Wait for notifications
        while True:
            try:
                n = self.get_msg()
            except Exception as e:
                LOG.info(f"Received exception for {self.purl.hostname}: {e}")
                self.close()
                return
            LOG.debug(f"Received notification: {n}")

            # Check the notification for mining.notify
            if "method" in n and n["method"] == "mining.notify":
                # Get the previous block hash
                prev_bh_stratum = struct.unpack(
                    "<IIIIIIII", bytes.fromhex(n["params"][1])
                )
                prev_bh = struct.pack(
                    "<IIIIIIII",
                    prev_bh_stratum[7],
                    prev_bh_stratum[6],
                    prev_bh_stratum[5],
                    prev_bh_stratum[4],
                    prev_bh_stratum[3],
                    prev_bh_stratum[2],
                    prev_bh_stratum[1],
                    prev_bh_stratum[0],
                ).hex()
                block_ver_hex = n["params"][5]
                block_ver = int.from_bytes(
                    bytes.fromhex(block_ver_hex), byteorder="big"
                )
                coinbase_part1 = n["params"][2]
                coinbase_part2 = n["params"][3]
                merkle_branches = n["params"][4]

                coinbase = None
                height = 0
                try:
                    coinbase = network.Tx.from_hex(coinbase_part1 + self.extranonce1 + "00"*self.extranonce2_length + coinbase_part2)
                    height = int.from_bytes(coinbase.txs_in[0].script[1:4], byteorder='little')
                except Exception as e:
                    print(e)

                nBits = n["params"][6]
                nTime = n["params"][7]
                clear_jobs = n["params"][8]
                txid = "empty block"
                if len(merkle_branches) > 0:
                    txid = bytes(reversed(bytes.fromhex(merkle_branches[0]))).hex()
                self.pipe_send.send(
                    {
                        "name": self.poolname,
                        "timestamp": time.time(),
                        "hostname": self.purl.hostname,
                        "port": self.purl.port,
                        "first_tx": txid,
                        "prev": prev_bh,
                        "coinbase1": coinbase_part1,
                        "coinbase2": coinbase_part2,
                        "coinbase": coinbase,
                        "extranonce1": self.extranonce1,
                        "extranonce2_length": self.extranonce2_length,
                        "coinbase_out": 0 if coinbase == None else coinbase.total_out(),
                        "height": height,
                        "bits": nBits,
                        "time": nTime,
                        "clear_jobs": clear_jobs, 
                        "branches": merkle_branches,
                        "conn_time": self.socket_open_time,
                    }
                )
                
    def run(self):
        try:
            self.get_stratum_work()
        except (ConnectionRefusedError, EOFError, socket.timeout):
            self.close()
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Subscribe to a Stratum and listen for new work"
    )
    parser.add_argument("url", help="The URL of the stratum server")
    parser.add_argument(
        "userpass", help="Username and password combination separated by a colon (:)"
    )
    parser.add_argument("--debug", help="Verbose debug logging", action="store_true")
    parser.add_argument("--logfile", help="Log file to log to")
    args = parser.parse_args()

    # Set logging level
    loglevel = logging.DEBUG# if args.debug else logging.INFO
    LOG.setLevel(loglevel)

    # Set the log file
    if args.logfile is not None:
        LOG.removeHandler(file_handler)
        logfile_handler = logging.FileHandler(filename=args.logfile)
        LOG.addHandler(logfile_handler)

    try:
        while True:
            w = Watcher(args.url, args.userpass)
            atexit.register(w.close)
            w.get_stratum_work()
            atexit.unregister(w.close)
    except KeyboardInterrupt:
        # When receiving a keyboard interrupt, do nothing and let atexit clean things up
        pass
