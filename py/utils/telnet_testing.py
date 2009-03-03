#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Sropulpof
# Copyright (C) 2008 Société des arts technoligiques (SAT)
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

"""
System test tools for two computers with the telnet UI.

Usage: trial test/test_twoboxes_network.py

pexpect expected strings are regular expression. See the re module.

IMPORTANT : you must first import this file from the telnet test, and 
then call this module's main() function.
""" 
import unittest
import pexpect
import os
import time
import sys
# ---------------------------------------------------------------------
# config 
SERVER_PORT = "14444"
SERVER_COMMAND = os.path.expanduser("./miville.py")
CLIENT_COMMAND = 'telnet localhost %s' % SERVER_PORT
#WAITING_DELAY = 1.0 # seconds before starting client after server start

VERBOSE_CLIENT = False
VERBOSE_SERVER = False
START_SERVER = True
# ---------------------------------------------------------------------
# startup poutine
try:
    REMOTE_HOST = os.environ['MIVILLE_TEST_REMOTE_HOST']
    REMOTE_CONTACT_NAME = os.environ['MIVILLE_TEST_REMOTE_CONTACT']
except KeyError:
    raise Exception("You must define the env variables defined in py/test/config_test.sh")

def get_color(color=None):
    """
    Returns ANSI escaped color code.
    Colors can be either 'BLUE' or 'MAGENTA' or None
    colors = {'BLACK':30, 'RED':31, 'GREEN':32, 'YELLOW':33, 'BLUE':34, 'MAGENTA':35, 'CYAN':36, 'WHITE':37}
    """
    colors = {'BLACK':30, 'RED':31, 'GREEN':32, 'YELLOW':33, 'BLUE':34, 'MAGENTA':35, 'CYAN':36, 'WHITE':37}
    try:
        s = str(colors[color]) + 'm'
    except KeyError:
        s = '0m' # default (usually white)
    return "\x1b[" + s

# ---------------------------------------------------------------------
# global variables for the telnet client and server child process
global_client = None
global_server = None
# ---------------------------------------------------------------------
class ProcessOutputLogger:
    """
    Class for output redirection of of process.

    Adds a prefix to each line printed by a spawn process.
    
    You must assign a reference to an instance of this class to 
    the logfile attribute of a spawn object
    """
    def __init__(self, prefixStr='', color='CYAN'):
        self.prefix = prefixStr
        self.buffer = []
        self.color = color

    def write(self, s):
        self.buffer.append(self.prefix + str(s).replace('\n', '\n' + self.prefix))

    def flush(self):
        #print "FLUSHING !"
        self.real_flush() # XXX ?

    def real_flush(self):
        """
        Actually flushes the buffer of this output buffer
        
        Adds some pretty colors as well.
        """
        sys.stdout.write(get_color(self.color))
        for s in self.buffer:
            sys.stdout.write(s)
        sys.stdout.write(get_color())
        sys.stdout.flush()
        self.buffer = []
        # print "" # TODO : get rid of this. flush() is not enough for some reason

# ---------------------------------------------------------------------
# functions
def println(s, endl=True):
    """
    Prints a line to standard output with a prefix.
    """
    if endl:
        print get_color('MAGENTA'), ">>>>", s, get_color()
    else:
        print ">>>>", s, # note the comma (",") at end of line

def start_process(command, isVerbose=False, logPrefix='', color='CYAN'):
    """
    Command is a string to execute
    
    Returns a pexpect.spawn object
    """
    try:
        directory = os.getcwd()
        if isVerbose:
            println('Current working dir: ' + directory)
            println('Starting \"%s\"' % command)
            process = pexpect.spawn(command, logfile=ProcessOutputLogger(logPrefix, color))
            #process = pexpect.spawn(command, logfile=sys.stdout)
        else:
            process = pexpect.spawn(command)
        time.sleep(1.0) # seconds
        if is_running(process) == False:
            raise Exception("Process is not running !")
            println("Process is not running !") # or raise error ?
            #die()
        else:
            return process
    except pexpect.ExceptionPexpect, e:
        println("Error starting client: heh" + str(e))
        raise
        #die()

def is_running(process):
    """
    Process is a pexpect.spawn object
    
    Returns boolean
    """
    if process is None:
        return False
    if process.isalive() == False:
        status = "no status available" 
        if process:
            status = process.status
        println("Error starting process: %s" % status)
        return False
    else:
        return process


def kill_process(process):
    """
    Kills a pexpect.spawn object
    
    See kill -l for flags
    """
    try:
        if is_running(process) == True:
            process.kill(15)
            time.sleep(2)
            if is_running(process) == True:
                process.kill(9)
    except Exception, e:
        print "Error killing process", e
        raise
    
def die():
    """
    Ends the programs with error flag.
    """
    println("EXITING")
    kill_process(global_client)
    kill_process(global_server)
    sys.exit(1)


# ---------------------------------------------------------------------
# System test classes
class TelnetBaseTest(unittest.TestCase):
    """
    Telnet system test case parent class
    """
    def setUp(self):
        """
        Starts a Telnet client for tests.
        """
        global global_server
        global global_client

        self.client = global_client
        self.server = global_server
        if is_running(self.server) is False:
            if START_SERVER:
                self.server = start_process(SERVER_COMMAND, VERBOSE_SERVER, "S>", 'CYAN')
        if is_running(self.client) is False:
            self.client = start_process(CLIENT_COMMAND, VERBOSE_CLIENT, "C>", 'MAGENTA')
        self.sleep()

    def tearDown(self):
        """
        Destructor for each test. 
        """
        pass

    def sleep(self, duration=0.1):
        """
        Waits a bit between each command.
        :param duration: float seconds
        """
        end = time.time() + duration
        while time.time() < end:
            time.sleep(0.001)
            try:
                self.client.logfile.real_flush()
            except AttributeError:
                pass
            try:
                self.server.logfile.real_flush()
            except AttributeError:
                pass

    def evalTest(self, index, message):
        """
        Fails a test, displaying a message, if the provided index resulting 
        from expect() matches some of the indices provided by expectTest()
        """
        self.assertEqual(index, 0, message)
        self.failIfEqual(index, 1, 'Problem : Unexpected EOF')
        self.failIfEqual(index, 2, 'Problem : Time out.')

    def expectTest(self, expected, message):
        """
        Fails a test if the expected regex value is not read from the client output.
        
        The expected value can be a string that is compiled to a regular expression (re)
        or the name of a Exception class.
        
        Succeeds otherwise.
        """
        # other listed expectations are child classes of Exception
        index = self.client.expect([expected, pexpect.EOF, pexpect.TIMEOUT], timeout=2) # 2 seconds max
        self.evalTest(index, message)


# ----------------------------- startup poutine -----------------------
# TODO: Fix the process.logfile not getting to sys.stdout
# TODO: If the test fails, check if client and server are still running.
def start():
    global global_server
    global global_client
    global VERBOSE_SERVER
    global VERBOSE_CLIENT
    global START_SERVER
    if VERBOSE_CLIENT:
        print "VERBOSE_CLIENT"
    if VERBOSE_SERVER:
        print "VERBOSE_SERVER"
        print "You should try this:"
        print "         tail -f /var/tmp/.sropulpof/sropulpof.log"
    if START_SERVER:
        global_server = start_process(SERVER_COMMAND, VERBOSE_SERVER, "S>", 'BLUE')
        # -----------------------------------  REMOVE ADDRESSBOOK DB
        try:
            #delete ~/.sropulpof/sropulpof.adb
            #orig_home = os.environ['HOME']
            os.environ['HOME'] = '/var/tmp'
            os.remove('/var/tmp/.sropulpof/sropulpof.adb')
            sys.stdout.write(get_color('MAGENTA'))
            print "using /var/tmp as a $HOME for .sropulpof/sropulpof.adb"
            sys.stdout.write(get_color())
        except Exception, e:
            print("Error removing old sropulpof.adb or setting HOME to /var/tmp." + str(e))
    time.sleep(2.0)  # !
    global_client = start_process(CLIENT_COMMAND, VERBOSE_CLIENT, "C>", 'CYAN')

