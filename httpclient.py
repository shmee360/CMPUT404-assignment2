#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Modifications copyright © 2021 Warren Stix

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse
from functools import reduce

S_TO_P = {'http': 80, 'https': 443}

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code:int=200, body:str=""):
        self.code = code
        self.body = body

class HTTPClient(object):
    user_agent = 'User-Agent: stix_req/1.0\r\n'

    @staticmethod
    def get_host_port(url: str):
        parse = urllib.parse.urlparse(url)
        port = S_TO_P[str(parse.scheme)] if parse.port is None else parse.port

        return (str(parse.hostname), port)

    @staticmethod
    def get_path(url: str) -> str:
        return urllib.parse.urlparse(url).path

    @staticmethod
    def get_argstr(args):
        if args is None:
            return ('', 0)

        argstr = reduce(lambda x, y: x + y[0] + '=' + y[1] + '&',
                        args.items(), '')[:-1]
        arglen = reduce(lambda x, y: x + len(y[0]) + len(y[1]) + 1,
                        args.items(), 0)

        return (argstr, arglen)

    def connect(self, host: str, port: int):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

    def get_code(self, data: str):
        return int(data.split()[1])

    def get_headers(self, data: str):
        for header in data.split('\r\n\r\n')[0].split('\r\n')[1:]:
            yield header.encode()

    def get_body(self, data: str) -> str:
        return data.split('\r\n\r\n')[1]
    
    def sendall(self, data: str):
        self.socket.sendall(data.encode('utf-8'))
        
    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock: socket.socket):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    def GET(self, url: str, args=None):
        path = self.get_path(url)
        (host, port) = self.get_host_port(url)
        (argstr, arglen) = self.get_argstr(args)

        req = (f'GET {path} HTTP/1.1\r\n'
               f'Host: {host}\r\n' +
               self.user_agent +
               'Accept: */*\r\n'
               f'Content-Length: {arglen}\r\n'
               'Connection: close\r\n'
               '\r\n' +
               argstr)

        self.connect(host, port)

        self.sendall(req)
        data = self.recvall(self.socket)
        
        self.close()

        code = self.get_code(data)
        body = self.get_body(data)

        return HTTPResponse(code, body)

    def POST(self, url: str, args=None):
        path = self.get_path(url)
        (host, port) = self.get_host_port(url)
        (argstr, arglen) = self.get_argstr(args)

        req = (f'POST {path} HTTP/1.1\r\n'
               f'Host: {host}\r\n' +
               self.user_agent +
               'Accept: */*\r\n'
               'Accept-Language: en-US,en;q=0.9\r\n'
               'Content-Type: application/x-www-form-urlencoded\r\n'
               f'Content-Length: {arglen}\r\n'
               'Connection: close\r\n'
               '\r\n' +
               argstr)

        self.connect(host, port)

        self.sendall(req)
        data = self.recvall(self.socket)
        
        self.close()

        code = self.get_code(data)
        body = self.get_body(data)

        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
