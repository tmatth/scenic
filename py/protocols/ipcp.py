#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Sropulpof
# Copyright (C) 2008 Société des arts technologiques (SAT)
# http://www.sat.qc.ca
# All rights reserved.
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Sropulpof is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sropulpof.  If not, see <http:#www.gnu.org/licenses/>.

import re
from types import NoneType, FunctionType

# twisted imports
from twisted.internet import reactor, protocol, defer
from twisted.protocols.basic import LineReceiver

# App imports
from utils import log

log = log.start('debug', 1, 0, 'icpc')


class IPCP(LineReceiver):
    def __init__(self):
        self.r = re.compile(r'("([^"\\]|\\.)*"|[^ ]+)')
        self.callbacks = {}

    def add_callback(self, cmd, name=None):
        if not name:
            name = cmd.im_class.__name__ + '/' + cmd.__name__
        if name not in self.callbacks:
            self.callbacks[name] = cmd
        else:
            log.debug('A callback with this name %s is already registered.' % name)
#        log.debug('Callback list: ' + repr(self.callbacks))
            
    def del_callback(self, name):
        if isinstance(name, FunctionType):
            name = cmd.im_class.__name__ + '/' + cmd.__name__
        if name in self.callbacks:
            del self.callbacks[name]
        else:
            log.debug('This callback %s is not registered.' % name)
#        log.debug('Callback list: ' + repr(self.callbacks))
              
    def connectionMade(self):
        log.info('Connection made to the server.')
    
    def lineReceived(self, line):
        args = self.r.findall(line)
        cmd = args[0][0]
        if cmd not in self.callbacks:
            log.debug('Command %s not in callback list.' % cmd)
        else:
            del args[0]
            for pos, arg in enumerate(args):
                arg = arg[0]
                if arg[0] == '"':
                    args[pos] = arg[1:-1].replace('\\\\', '\\') \
                                         .replace("\\'", "'") \
                                         .replace('\\"', '"')
                elif arg.isdigit():
                    args[pos] = int(arg)
                else:
                    try:
                        args[pos] = float(arg)
                    except:
                        log.debug('Invalid type for received argument %s.' % arg)
            log.debug("Received: " + cmd + repr(args))
            self.callbacks[cmd](*args)
    
    def send_cmd(self, cmd, *args):
        line = []
        line.append(cmd)
        for arg in args:
            if isinstance(arg, tuple):
                parg = self._process_arg(arg[1])
                if parg:
                    line.append(arg[0] + '=' + parg)
            else:
                parg = self._process_arg(arg)
                if parg:
                    line.append(parg)
        self.sendLine(' '.join(line))
        log.debug('Sending: ' + ' '.join(line))

    def _process_arg(self, arg):
        if isinstance(arg, int) or isinstance(arg, float):
            return str(arg)
        elif isinstance(arg, unicode):
            return '"%s"' % arg.encode('ascii', 'backslashreplace') \
                                    .replace('\\', '\\\\') \
                                    .replace("'", "\\'") \
                                    .replace('"', '\\"')
        elif isinstance(arg, str):
            return '"%s"' % arg.replace('\\', '\\\\') \
                                    .replace("'", "\\'") \
                                    .replace('"', '\\"')
        elif not isinstance(arg, NoneType):
            log.debug('Invalid type (%s) for argument %s to send.' % (type(arg), arg))
        return None

    def connectionLost(self, reason=protocol.connectionDone):
        log.info('Lost the server connection.')
        
      
def connect(addr, port, timeout=2, bindAddress=None):
    client_creator = protocol.ClientCreator(reactor, IPCP)
    deferred = client_creator.connectTCP(addr, port, timeout, bindAddress)
    return deferred

def connection_failed(protocol):
    log.warning("Connection failed! %s" % protocol.getErrorMessage())        
        


def grrr(test):
    print test
    print "yes!"

def test(arg1, arg2, arg3):
    print "perte"
    print arg1, arg2, arg3

# When connected, send a line
def connectionReady(protocol):
    protocol.add_callback('You', test)
    protocol.connectionLost = grrr
    protocol.sendLine('Hey there')
    protocol.send_cmd('test', 23.3, 34, 'gros bouton', 1)
    reactor.callLater(10, protocol.sendLine, 'Coco')
    reactor.callLater(20, reactor.stop)


if __name__ == "__main__":
    # Client example
    # Create creator and connect
    deferred = connect('127.0.0.1', 22222)
    deferred.addCallback(connectionReady)
    deferred.addErrback(connection_failed)
    reactor.run()
