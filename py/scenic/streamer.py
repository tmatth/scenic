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
Manages local streamer processes.
"""

from scenic import process
from scenic import sig
from scenic import dialogs
from scenic.internationalization import _

class StreamerManager(object):
    """
    Manages local streamer processes.
    """
    def __init__(self, app):
        self.app = app
        # commands
        self.milhouse_recv_cmd = None
        self.milhouse_send_cmd = None
        self.sender = None
        self.receiver = None
        self.midi_receiver = None
        self.midi_sender = None
        self.state = process.STATE_STOPPED
        self.state_changed_signal = sig.Signal()
        # for stats
        self.session_details = None # either None or a big dict
        self.rtcp_stats = None # either None or a big dict
        self.error_messages = None # either None or a big dict

    def _calculate_packet_loss(self):
        """
        Takes the last value and the current for packets lost and total packets.
        Calculates the percent of packet loss : 

        delta loss / delta sent
        
        Multiplied by 100 to get a percentage.
        """
        #TODO:
        video_lost = self.rtcp_stats["send"]["video"]["packets-lost"]
        video_sent = self.rtcp_stats["send"]["video"]["packets-sent"]
        audio_lost = self.rtcp_stats["send"]["audio"]["packets-lost"]
        audio_sent = self.rtcp_stats["send"]["audio"]["packets-sent"]
        video_lost_previous = self.rtcp_stats["send"]["video"]["packets-lost-previous"]
        video_sent_previous = self.rtcp_stats["send"]["video"]["packets-sent-previous"]
        audio_lost_previous = self.rtcp_stats["send"]["audio"]["packets-lost-previous"]
        audio_sent_previous = self.rtcp_stats["send"]["audio"]["packets-sent-previous"]
        
        if self.rtcp_stats["send"]["video"]["packets-lost-got-new"] and self.rtcp_stats["send"]["video"]["packets-sent-got-new"]:
            self.rtcp_stats["send"]["video"]["packets-lost-got-new"] = False
            self.rtcp_stats["send"]["video"]["packets-sent-got-new"] = False
            diff_video_sent = float(video_sent - video_sent_previous)
            if diff_video_sent != 0: # avoid division by zero
                video_packets_loss = float(video_lost - video_lost_previous) / diff_video_sent * 100
                if video_packets_loss >= 0.0:   # FIXME: temporary fix to avoid occasional bogus percentages
                    self.rtcp_stats["send"]["video"]["packets-loss-percent"] =  video_packets_loss
                    print("Video packet loss : %s" % (video_packets_loss))
            self.rtcp_stats["send"]["video"]["packets-lost-previous"] = video_lost
            self.rtcp_stats["send"]["video"]["packets-sent-previous"] = video_sent
        if self.rtcp_stats["send"]["audio"]["packets-lost-got-new"] and self.rtcp_stats["send"]["audio"]["packets-sent-got-new"]:
            self.rtcp_stats["send"]["audio"]["packets-lost-got-new"] = False
            self.rtcp_stats["send"]["audio"]["packets-sent-got-new"] = False
            diff_audio_sent = float(audio_sent - audio_sent_previous)
            if diff_audio_sent != 0: # avoid division by zero
                audio_packets_loss = float(audio_lost - audio_lost_previous) / diff_audio_sent * 100
                if audio_packets_loss >= 0.0:   # FIXME: temporary fix to avoid occasional bogus percentages
                    self.rtcp_stats["send"]["audio"]["packets-loss-percent"] = audio_packets_loss
                    print("Audio packet loss : %s" % (audio_packets_loss))
            self.rtcp_stats["send"]["audio"]["packets-lost-previous"] = audio_lost
            self.rtcp_stats["send"]["audio"]["packets-sent-previous"] = audio_sent

    def _gather_config_to_stream(self, addr):
        """
        Gathers all settings in a big dict.
        
        Useful for feedback to the user.
        """
        contact_name = addr
        contact = self.app._get_contact_by_addr(addr)
        if contact is not None:
            contact_name = contact["name"]
        
        remote_config = self.app.remote_config # FIXME: should the remote config be passed as a param to this method?
        send_width, send_height = self.app.config.video_capture_size.split("x")
        receive_width, receive_height = remote_config["video"]["capture_size"].split("x")
        
        # MIDI
        midi_send_enabled = self.app.config.midi_send_enabled and remote_config["midi"]["recv_enabled"]
        midi_recv_enabled = self.app.config.midi_recv_enabled and remote_config["midi"]["send_enabled"]
        midi_input_device = self.app.config.midi_input_device
        midi_output_device = self.app.config.midi_output_device
        
        print "remote_config:", remote_config
        
        self.session_details = {
            "peer": {
                "address": addr,
                "name": contact_name,
                },
            # ----------------- send ---------------
            "send": {
                "video": {
                    # Decided locally:
                    "source": self.app.config.video_source,
                    "device": self.app.config.video_device,
                    "width": int(send_width), # int
                    "height": int(send_height), # int
                    "aspect-ratio": self.app.config.video_aspect_ratio,
                    
                    # Decided by remote peer:
                    "port": remote_config["video"]["port"], 
                    "bitrate": remote_config["video"]["bitrate"], 
                    "codec": remote_config["video"]["codec"], 
                },
                
                "audio": {
                    # decided locally:
                    "source": self.app.config.audio_source,

                    # Decided by remote peer:
                    "numchannels": remote_config["audio"]["numchannels"],
                    "codec": remote_config["audio"]["codec"],
                    "port": remote_config["audio"]["port"], 
                }, 
                "midi": {
                    "enabled": midi_send_enabled,
                    "input_device": midi_input_device,
                    "port": remote_config["midi"]["port"]
                }
            },
            # -------------------- recv ------------
            "receive": {
                "video": {
                    # decided locally:
                    "sink": self.app.config.video_sink,
                    "port": str(self.app.recv_video_port), #decided by the app
                    "codec": self.app.config.video_codec,
                    "deinterlace": self.app.config.video_deinterlace, # bool
                    "window-title": "\"From %s\"" % (contact_name), #TODO: i18n
                    "jitterbuffer": self.app.config.video_jitterbuffer, 
                    "fullscreen": self.app.config.video_fullscreen, # bool
                    "display": self.app.config.video_display,
                    "bitrate": self.app.config.video_bitrate, # float
                    
                    # Decided by remote peer:
                    "aspect-ratio": remote_config["video"]["aspect_ratio"],
                    "width": int(receive_width), # int
                    "height": int(receive_height), # int
                },
                "audio": {
                    # decided locally:
                    "numchannels": self.app.config.audio_channels, # int
                    "codec": self.app.config.audio_codec, 
                    "port": self.app.recv_audio_port,
                    "sink": self.app.config.audio_sink
                },
                "midi": {
                    "enabled": midi_recv_enabled,
                    "jitterbuffer": self.app.config.midi_jitterbuffer,
                    "output_device": midi_output_device,
                    "port": str(self.app.recv_midi_port),
                }
            }
        }
        if self.session_details["send"]["video"]["source"] != "v4l2src":
            self.session_details["send"]["video"]["device"] = None
        if self.session_details["send"]["video"]["codec"] == "theora":
            self.session_details["send"]["video"]["bitrate"] = None
        print(str(self.session_details))
        
    def start(self, host):
        """
        Starts the sender and receiver processes.
        
        @param host: str ip addr
        Raises a RuntimeError if a sesison is already in progress.
        """
        if self.state != process.STATE_STOPPED:
            raise RuntimeError("Cannot start streamers since they are %s." % (self.state)) # the programmer has done something wrong if we're here.
        
        self._gather_config_to_stream(host)
        details = self.session_details

        # ------------------ send ---------------
        # every element in the lists must be strings since we join them .
        # int elements are converted to str.
        self.milhouse_send_cmd = [
            "milhouse", 
            '--sender', 
            '--address', details["peer"]["address"],
            '--videosource', details["send"]["video"]["source"],
            '--videocodec', details["send"]["video"]["codec"],
            '--videoport', str(details["send"]["video"]["port"]),
            '--width', str(details["send"]["video"]["width"]), 
            '--height', str(details["send"]["video"]["height"]),
            '--aspect-ratio', str(details["send"]["video"]["aspect-ratio"]),
            '--audiosource', details["send"]["audio"]["source"],
            '--numchannels', str(details["send"]["audio"]["numchannels"]),
            '--audiocodec', details["send"]["audio"]["codec"],
            '--audioport', str(details["send"]["audio"]["port"]),
            ]
        if details["send"]["video"]["source"] == "v4l2src":
            dev = self.app.parse_v4l2_device_name(details["send"]["video"]["device"])
            if dev is None:
                print "v4l2 device is not found !!!!"
            else:
                v4l2_dev_name = dev["name"]
            self.milhouse_send_cmd.extend(["--videodevice", v4l2_dev_name])
        if details["send"]["video"]["codec"] != "theora":
            self.milhouse_send_cmd.extend(['--videobitrate', str(int(details["send"]["video"]["bitrate"] * 1000000))])

        # ------------------- recv ----------------
        self.milhouse_recv_cmd = [
            "milhouse",
            '--receiver', 
            '--address', details["peer"]["address"],
            '--videosink', details["receive"]["video"]["sink"],
            '--videocodec', details["receive"]["video"]["codec"],
            '--videoport', str(details["receive"]["video"]["port"]),
            '--jitterbuffer', str(details["receive"]["video"]["jitterbuffer"]),
            '--width', str(details["receive"]["video"]["width"]),
            '--height', str(details["receive"]["video"]["height"]),
            '--aspect-ratio', details["receive"]["video"]["aspect-ratio"],
            '--audiosink', details["receive"]["audio"]["sink"],
            '--numchannels', str(details["receive"]["audio"]["numchannels"]),
            '--audiocodec', details["receive"]["audio"]["codec"],
            '--audioport', str(details["receive"]["audio"]["port"]),
            '--window-title', details["receive"]["video"]["window-title"],
            '--display', details["receive"]["video"]["display"],
            ]
        if details["receive"]["video"]["fullscreen"]:
            self.milhouse_recv_cmd.append('--fullscreen')
        if details["receive"]["video"]["deinterlace"]:
            self.milhouse_recv_cmd.append('--deinterlace')

        # setting up
        self.rtcp_stats = {
            "send": {
                "video": {
                    "packets-lost": 0,
                    "packets-sent": 0,
                    "packets-lost-previous": 0,
                    "packets-sent-previous": 0,
                    "packets-lost-got-new": False,
                    "packets-sent-got-new": False,
                    "packets-loss-percent": 0.0,
                    "jitter": 0,
                    "bitrate": None,
                    "connected": False
                },
                "audio": {
                    "packets-lost": 0,
                    "packets-sent": 0,
                    "packets-lost-previous": 0,
                    "packets-sent-previous": 0,
                    "packets-lost-got-new": False,
                    "packets-sent-got-new": False,
                    "packets-loss-percent": 0.0,
                    "jitter": 0,
                    "bitrate": None,
                    "connected": False
                }
            },
            "receive": {
                "video": {
                    "connected": False,
                    "bitrate": None 
                },
                "audio": {
                    "connected": False,
                    "bitrate": None 
                }
            }
        }
        self.error_messages = {
            "send": [], # list of strings
            "receive": [], # list of strings
            }
        # every element in the lists must be strings since we join them 
        # ---- audio/video receiver ----
        recv_cmd = " ".join(self.milhouse_recv_cmd)
        self.receiver = process.ProcessManager(command=recv_cmd, identifier="receiver")
        self.receiver.state_changed_signal.connect(self.on_process_state_changed)
        self.receiver.stdout_line_signal.connect(self.on_receiver_stdout_line)
        self.receiver.stderr_line_signal.connect(self.on_receiver_stderr_line)
        # ---- audio/video sender ----
        send_cmd = " ".join(self.milhouse_send_cmd)
        self.sender = process.ProcessManager(command=send_cmd, identifier="sender")
        self.sender.state_changed_signal.connect(self.on_process_state_changed)
        self.sender.stdout_line_signal.connect(self.on_sender_stdout_line)
        self.sender.stderr_line_signal.connect(self.on_sender_stderr_line)
        
        midi_recv_enabled = self.session_details["receive"]["midi"]["enabled"]
        midi_send_enabled = self.session_details["send"]["midi"]["enabled"]
        
        if midi_recv_enabled:
            midi_out_device = self.app.parse_midi_device_name(details["receive"]["midi"]["output_device"], is_input=False)
            #TODO: check if is None
            midi_recv_args = [
                "midistream",
                "--address", details["peer"]["address"],
                "--receiving-port", str(details["receive"]["midi"]["port"]),
                "--jitter-buffer", str(details["receive"]["midi"]["jitterbuffer"]),
                "--output-device", str(midi_out_device["number"])
                ]
                #"--verbose",
            midi_recv_command = " ".join(midi_recv_args) 
            self.midi_receiver = process.ProcessManager(command=midi_recv_command, identifier="midi_receiver")
            self.midi_receiver.state_changed_signal.connect(self.on_process_state_changed)
            self.midi_receiver.stdout_line_signal.connect(self.on_midi_stdout_line)
            self.midi_receiver.stderr_line_signal.connect(self.on_midi_stderr_line)
        
        if midi_send_enabled:
            midi_in_device = self.app.parse_midi_device_name(details["receive"]["midi"]["input_device"], is_input=True)
            #TODO: check if is None
            midi_send_args = [
                "midistream",
                "--address", details["peer"]["address"],
                "--sending-port", str(details["send"]["midi"]["port"]),
                "--input-device", str(midi_in_device["number"])
                ]
                #"--verbose",
            midi_send_command = " ".join(midi_send_args) 
            self.midi_sender = process.ProcessManager(command=midi_send_command, identifier="midi_sender")
            self.midi_sender.state_changed_signal.connect(self.on_process_state_changed)
            self.midi_sender.stdout_line_signal.connect(self.on_midi_stdout_line)
            self.midi_sender.stderr_line_signal.connect(self.on_midi_stderr_line)
        
        # starting
        self._set_state(process.STATE_STARTING)
        print "$", send_cmd
        self.sender.start()
        print "$", recv_cmd
        self.receiver.start()
        if midi_recv_enabled:
            self.midi_receiver.start()
        if midi_send_enabled:
            self.midi_sender.start()

    def on_midi_stdout_line(self, process_manager, line):
        print process_manager.identifier, line

    def on_midi_stderr_line(self, process_manager, line):
        print process_manager.identifier, line

    def on_receiver_stdout_line(self, process_manager, line):
        """
        Handles a new line from our receiver process' stdout
        """
        if "stream connected" in line:
            if "audio" in line:
                self.rtcp_stats["receive"]["audio"]["connected"] = True
            elif "video" in line:
                self.rtcp_stats["receive"]["video"]["connected"] = True
        elif "BITRATE" in line:
            if "video" in line:
                self.rtcp_stats["receive"]["video"]["bitrate"] = int(line.split(":")[-1])
            elif "audio" in line:
                self.rtcp_stats["receive"]["audio"]["bitrate"] = int(line.split(":")[-1])
        else:
            print "%9s stdout: %s" % (self.receiver.identifier, line)

    def on_receiver_stderr_line(self, process_manager, line):
        """
        Handles a new line from our receiver process' stderr
        """
        print "%9s stderr: %s" % (self.receiver.identifier, line)
        if "CRITICAL" in line or "ERROR" in line:
            self.error_messages["receive"].append(line)
    
    def on_sender_stdout_line(self, process_manager, line):
        """
        Handles a new line from our receiver process' stdout
        """
        print "%9s stdout: %s" % (self.sender.identifier, line)
        try:
            if "PACKETS-LOST" in line:
                if "video" in line:
                    self.rtcp_stats["send"]["video"]["packets-lost"] = int(line.split(":")[-1])
                    self.rtcp_stats["send"]["video"]["packets-lost-got-new"] = True
                elif "audio" in line:
                    self.rtcp_stats["send"]["audio"]["packets-lost"] = int(line.split(":")[-1])
                    self.rtcp_stats["send"]["audio"]["packets-lost-got-new"] = True
                #self._calculate_packet_loss()
            if "PACKETS-SENT" in line:
                if "video" in line:
                    self.rtcp_stats["send"]["video"]["packets-sent"] = int(line.split(":")[-1])
                    self.rtcp_stats["send"]["video"]["packets-sent-got-new"] = True
                elif "audio" in line:
                    self.rtcp_stats["send"]["audio"]["packets-sent"] = int(line.split(":")[-1])
                    self.rtcp_stats["send"]["audio"]["packets-sent-got-new"] = True
                #self._calculate_packet_loss()
            elif "JITTER" in line:
                if "video" in line:
                    self.rtcp_stats["send"]["video"]["jitter"] = int(line.split(":")[-1])
                elif "audio" in line:
                    self.rtcp_stats["send"]["audio"]["jitter"] = int(line.split(":")[-1])
            elif "BITRATE" in line:
                if "video" in line:
                    self.rtcp_stats["send"]["video"]["bitrate"] = int(line.split(":")[-1])
                elif "audio" in line:
                    self.rtcp_stats["send"]["audio"]["bitrate"] = int(line.split(":")[-1])
            elif "connected" in line:
                if "video" in line:
                    self.rtcp_stats["send"]["video"]["connected"] = True
                elif "audio" in line:
                    self.rtcp_stats["send"]["audio"]["connected"] = True
        except ValueError, e:
            print(e)

    def on_sender_stderr_line(self, process_manager, line):
        """
        Handles a new line from our receiver process' stderr
        """
        print "%9s stderr: %s" % (self.sender.identifier, line)
        if "CRITICAL" in line or "ERROR" in line:
            self.error_messages["send"].append(line)

    def is_busy(self):
        """
        Retuns True if a streaming session is in progress.
        """
        return self.state != process.STATE_STOPPED

    def get_all_streamer_process_managers(self):
        """
        Returns all the current streaming process managers for the current session.
        @rtype: list
        """
        ret = [self.sender, self.receiver]
        if self.session_details["receive"]["midi"]["enabled"]:
            ret.append(self.midi_receiver)
        if self.session_details["send"]["midi"]["enabled"]:
            ret.append(self.midi_sender)
        return ret

    def on_process_state_changed(self, process_manager, process_state):
        """
        Slot for the ProcessManager.state_changed_signal
        Calls stop() if one of the processes crashed.
        """
        print process_manager, process_state
        if process_state == process.STATE_RUNNING:
            # As soon as one is running, set our state to running
            if self.state == process.STATE_STARTING:
                self._set_state(process.STATE_RUNNING)
        elif process_state == process.STATE_STOPPING:
            pass
        elif process_state == process.STATE_STARTING:
            pass
        elif process_state == process.STATE_STOPPED:
            # As soon as one crashes or is not able to start, stop all streamer processes.
            if self.state in [process.STATE_RUNNING, process.STATE_STARTING]:
                print("A streamer process died. Stopping the local streamer manager.")
                self.stop() # sets self.state to STOPPING
            # Next, if all streamers are dead, we can say this manager is stopped
            if self.state == process.STATE_STOPPING:
                one_is_left = False
                for proc in self.get_all_streamer_process_managers():
                    if process_manager is not proc and proc.state != process.STATE_STOPPED:
                        print("Streamer process %s is not dead, so we are not done stopping. Its state is %s." % (proc, proc.state))
                        one_is_left = True
                if not one_is_left:
                    print "Setting streamers manager to STOPPED"
                    self._set_state(process.STATE_STOPPED)

    def on_stopped(self):
        """
        When the state changes to stopped, 
         * check for errors and display them to the user.
        """
        msg = ""
        details = ""
        show_error_dialog = False
        #TODO: internationalize
        print("All streamers are stopped.")
        print("Error messages for this session: %s" % (self.error_messages))
        if len(self.error_messages["send"]) != 0:
            details += _("Errors from local sender:") + "\n"
            for line in self.error_messages["send"]:
                details += " * " + line + "\n"
            show_error_dialog = True
        if len(self.error_messages["receive"]) != 0:
            details += _("Errors from local receiver:") + "\n"
            for line in self.error_messages["receive"]:
                details += " * " + line + "\n"
            show_error_dialog = True
        if show_error_dialog:
            msg = _("Some errors occured during the audio/video streaming session.")
            dialogs.ErrorDialog.create(msg, parent=self.app.gui.main_window, details=details)
        # TODO: should we set all our process managers to None
        for proc in self.get_all_streamer_process_managers():
            proc = None
        print "should all be None:", self.get_all_streamer_process_managers()
    
    def _set_state(self, new_state):
        """
        Handles state changes.
        """
        if self.state != new_state:
            self.state_changed_signal(self, new_state)
            self.state = new_state
            if new_state == process.STATE_STOPPED:
                self.on_stopped()
        else:
            raise RuntimeError("Setting state to %s, which is already the current state." % (self.state))
            
    def stop(self):
        """
        Stops the sender and receiver processes.
        Does not send any message to the remote peer ! This must be done somewhere else.
        """
        #TODO: return a deferred
        # stopping
        if self.state in [process.STATE_RUNNING, process.STATE_STARTING]:
            self._set_state(process.STATE_STOPPING)
            for proc in self.get_all_streamer_process_managers():
                if proc is not None:
                    if proc.state != process.STATE_STOPPED and proc.state != process.STATE_STOPPING:
                        proc.stop()
