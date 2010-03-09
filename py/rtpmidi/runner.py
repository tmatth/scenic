#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Scenic
# Copyright (C) 2008 Société des arts technologiques (SAT)
# http://www.sat.qc.ca
# All rights reserved.
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Scenic is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Scenic. If not, see <http://www.gnu.org/licenses/>.
"""
Main runner of the app is the run() function.
"""
import os
import sys
import signal
from twisted.internet import reactor
from optparse import OptionParser

from rtpmidi.engines.midi.midi_session import MidiSession
from rtpmidi.protocols.rtp.rtp_control import RTPControl
from rtpmidi import utils

class Config(object):
    """
    Configuration for the application.
    """
    def __init__(self):
        # str:
        self.peer_address = None
        # int:
        self.receiving_port = None
        self.sending_port = None
        self.input_device = None
        self.output_device = None
        self.latency = 20 # ms
        self.jitter_buffer = 10 # ms
        # bool:
        self.safe_keyboard = False
        self.disable_recovery_journal = False
        self.follow_standard = False
        self.verbose = False

def sigint_handler(signum, frame):
    """
    SIGINT handler.
    """
    global launch_flag
    print "\nSIGINT caught! Shutting down midi stream module."
    RTPControl().stop()
    reactor.stop()

def list_midi_devices():
    """
    Lists MIDI devices.
    """
    rtp_control = RTPControl()
    midi_session = rtp_control.add_session(MidiSession("127.0.0.1", rport=1, sport=1))
    midi_session = rtp_control.get_session(midi_session)
    dev_in, dev_out = midi_session.get_devices()
    print "List of MIDI devices:"
    print "    Input devices:"
    print "    --------------"
    for dev in dev_in:
        print "     * input  %2s %30s" % (dev[0], dev[1]),
        if dev[2] == 1:
            print "  [open]"
        else:
            print "  [closed]"
    print "    Output devices:"
    print "    ---------------"
    for dev in dev_out:
        print "     * output %2s %30s" % (dev[0], dev[1]),
        if dev[2] == 1:
            print "  [open]"
        else:
            print "  [closed]"

def run(version):
    """
    MAIN of the application.
    Parses the arguments and runs the app.
    @param version: Version of the app. (str)
    """
    description = "Creates a MIDI RTP stream between two hosts, uni or bi-directionnal."
    details = """Example: midistream -a 10.0.1.29 -r 44000 -s 44000 -i 1 -o 0

This command creates a bi-directional connection with 10.0.1.29 on port 44000, midi device 1 is the source for sending data, and all received data are sent to midi device 0.
Caution: If the stream is bi-directionnal receiving port and sending port must be equal.""" 
    parser = OptionParser(usage="%prog", version=version, description=description, epilog=details)
    parser.add_option("-a", "--address", type="string", help="Specify the address of the peer (mandatory)")
    parser.add_option("-l", "--list-devices", action="store_true", help="Show a complete list of midi devices")
    parser.add_option("-s", "--sending-port", type="int", help="Select the sending port. Must be used the --input-device option.")
    parser.add_option("-r", "--receiving-port", type="int", help="Select the listening port. Must be used the --output-device option.")
    parser.add_option("-o", "--output-device", type="int", help="Select a midi output device. (sink) Must be used with the --receiving-port option.")
    parser.add_option("-i", "--input-device", type="int", help="Select a midi input device. (source) Must be used with the --sending-port option.")
    parser.add_option("-L", "--latency", type="int", help="Specify the latency (in ms) of the midi out device (default is 20)")
    parser.add_option("-b", "--jitter-buffer", type="int", help="Specify the jitter buffer size in ms (default is 10)")
    parser.add_option("-k", "--safe-keyboard", action="store_true", help="Take care of note ON/OFF alternating, usefull if several notes in a ms (experimental)"),
    parser.add_option("-j", "--disable-recovery-journal", action="store_true", help="DISABLE recovery journal (journal provide note recovery when a packet is lost, so at your own risks!)"),
    parser.add_option("-f", "--follow-standard", action="store_true", help="Take care of MIDI standard (ex: omni on) in recovery journal (experimental)"),
    parser.add_option("-v", "--verbose", action="store_true", help="Enables a verbose output"),
    (options, args) = parser.parse_args()
    
    config = Config()
    
    # FIXME: use optparse
    if options.list_devices:
        list_midi_devices()
        sys.exit(0)
    # bool options:
    if options.disable_recovery_journal:
        config.disable_recovery_journal = True
    if options.follow_standard:
        config.follow_standard = True
    if options.safe_keyboard:
        config.safe_keyboard = True
    if options.verbose:
        config.verbose = True
    # int options:
    if options.latency is not None:
        config.latency = options.latency
    if options.input_device is not None:
        config.input_device = options.input_device
    if options.output_device is not None:
        config.output_device = options.output_device
    if options.jitter_buffer is not None:
        config.jitter_buffer = options.jitter_buffer
    if options.receiving_port is not None:
        config.receiving_port = options.receiving_port
        if not utils.check_port(config.receiving_port):
            print "Incorrect receiving port number:", config.receiving_port
            parser.print_usage()
            sys.exit(2)
    if options.sending_port is not None:
        config.sending_port = options.sending_port
        if not utils.check_port(config.sending_port):
            print "Incorrect sending port number:", config.sending_port
            parser.print_usage()
            sys.exit(2)
    # string options:
    if options.address is not None:
        config.peer_address = options.address
        if not utils.check_ip(config.peer_address):
            print "Wrong ip address format: ", config.peer_address
            sys.exit(2)
    # validate logic in options : -----------------
    if config.peer_address is None:
        print "Error: You must specify a peer address."
        parser.print_usage()
        sys.exit(2)
    if config.sending_port is not None:
        if config.input_device is None:
            print "Error: You must specify an input device number if in sending mode."
            parser.print_usage()
            sys.exit(2)
    if config.receiving_port is not None:
        if config.output_device is None:
            print "Error: You must specify an output device number if in receiving mode."
            parser.print_usage()
            sys.exit(2)
    if config.receiving_port is None and config.sending_port is None:
        print "Error: You must choose either the sending or receiving mode."
        parser.print_usage()
        sys.exit(2)
    if config.sending_port is not None and config.receiving_port is not None:
        if config.sending_port != config.receiving_port:
            print "Error: receiving port and sending port must be equal if both specified."
            parser.print_usage()
            sys.exit(2)
    # start the app:
    midi_session_c = RTPControl().add_session(MidiSession(
        config.peer_address, 
        sport=config.sending_port, 
        rport=config.receiving_port, 
        latency=config.latency, 
        jitter_buffer_size=config.jitter_buffer, 
        safe_keyboard=config.safe_keyboard,
        recovery=config.disable_recovery_journal,
        follow_standard=config.follow_standard,
        verbose=config.verbose))
    midi_session = RTPControl().get_session(midi_session_c)
    dev_in, dev_out = midi_session.get_devices()
    if config.input_device is not None:
        res = midi_session.set_device_in(config.input_device)
        if not res:
            print("Could not start session with input device %s" % (config.input_device))
            sys.exit(2)
    if config.output_device is not None:
        res = midi_session.set_device_out(config.output_device)
        if not res:
            print("Could not start session with output device %s" % (config.output_device))
            sys.exit(2)
    RTPControl().start_session(midi_session_c)
    signal.signal(signal.SIGINT, sigint_handler)
    reactor.run()