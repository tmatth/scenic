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
Scenic GTK GUI.

Negotiation is done as follow:
------------------------------
 * {"msg":"INVITE", "videoport":10000, "audioport":11000, "sid":0, "please_send_to_port":999}
 * {"msg":"ACCEPT", "videoport":10000, "audioport":11000, "sid":0}
 * {"msg":"REFUSE", "sid":0}
 * {"msg":"ACK", "sid":0}
 * {"msg":"BYE", "sid":0}
 * {"msg":"OK", "sid":0}

Former Notes
------------
 * voir si il faut gerer une demande de connexion alors que c'est deja connecte
 * voir si le bouton "cancel" est necesaire dans la fenetre "contacting" :
 *   - si oui il faudra trouver un moyen de faire la connection sans bloquer l'interface
 *   (thread, idle gtk ou io_watch?)
 * en prod regler test a 0
 * bug pour setter le bouton par defaut quand on change de tab. Il faut que le tab est le focus pour que ca marche. Pourtant le "print" apparait ???
"""
### CONSTANTS ###
__version__ = "0.1.0"
APP_NAME = "scenic"

### MODULES IMPORTS  ###

import sys
import os
import smtplib
from scenic import data
PACKAGE_DATA = os.path.dirname(data.__file__)
try:
    import gtk
    import gtk.glade
    import gobject
except ImportError, e:
    print "Could not load GTK or glade. Install python-gtk2 and python-glade2.", str(e)
    sys.exit(1)
# JSON import:
try:
    import json # python 2.6
except ImportError:
    import simplejson as json # python 2.4 to 2.5
try:
    _tmp = json.loads
except AttributeError:
    import warnings
    warnings.warn("Use simplejson, not the old json module.")
    sys.modules.pop('json') # get rid of the bad json module
    import simplejson as json

### MULTILINGUAL SUPPORT ###
DIR = os.path.join(PACKAGE_DATA, "locale")
import gettext
_ = gettext.gettext
gettext.bindtextdomain(APP_NAME, DIR)
gettext.textdomain(APP_NAME)
gtk.glade.bindtextdomain(APP_NAME, DIR)
gtk.glade.textdomain(APP_NAME)

from scenic import communication
from scenic import process # just for constants
from scenic.streamer import StreamerManager
from twisted.internet import defer
from twisted.internet import error
from twisted.internet import reactor

class Config(object):
    """
    Class attributes are default.
    """
    # Default values
    negotiation_port = 17446 # sending/receiving TCP messages on it.
    smtpserver = "smtp.sat.qc.ca"
    emailinfo = "maugis@sat.qc.ca"
    audio_input = "jackaudiosrc"
    audio_output = "jackaudiosink"
    audio_codec = "raw"
    audio_channels = 8
    video_input = "v4l2src"
    video_device = "/dev/video0"
    video_output = "xvimagesink"
    video_codec = "mpeg4"
    video_bitrate = "3000000"
    send_video_port = 8000
    recv_video_port = 8000
    send_audio_port = send_video_port + 10
    recv_audio_port = recv_video_port + 10
    bandwidth = 30
    
    def __init__(self):
        config_file = 'maugis.cfg'
        if os.path.isfile('/etc/' + config_file):
            config_dir = '/etc'
        else:
            config_dir = os.environ['HOME'] + '/.maugis'
        self._config_path = os.path.join(config_dir, config_file)
        if os.path.isfile(self._config_path):
            self._read()
        else:
            if not os.path.isdir(config_dir):
                os.mkdir(config_dir)
            self._write()

    def _write(self):
        """
        Comments out the options that have not been changed from default.
        """
        config_str = _("# Configuration written by %(app)s %(version)s\n") % {'app': APP_NAME, 'version': __version__}
        for c in dir(self):
            if c[0] != '_' and hasattr(self, c):
                inst_attr = getattr(self, c)
                if inst_attr == getattr(Config, c):
                    comment = "# "
                else:
                    comment = ""
                config_str += "\n" + comment + c + "=" + str(inst_attr)
        config_file = file(self._config_path, "w")
        config_file.write(config_str)
        config_file.close()

    def _read(self):
        config_file  = file(self._config_path, "r")
        for line in config_file:
            line = line.strip()
            if line and line[0] != "#" and len(line) > 2:
                try:
                    tokens = line.split("=")
                    k = tokens[0].strip()
                    v = tokens[1].strip()
                    if v.isdigit():
                        v = int(v)
                    else:
                        v = str(v)
                    setattr(self, k, v)
                    print("Setting config %s = %s" % (k, v))
                except Exception, e:
                    print str(e)
        config_file.close()

class AddressBook(object):
    """
    READING & WRITING ADDRESS BOOK FILE 
    """
    def __init__(self):
        self.contact_list = []
        self.selected = 0
        #FIXME: do not hard code
        self.contacts_file_name = os.path.join(os.environ['HOME'], '.maugis/contacts.json')
        self.SELECTED_KEYNAME = "selected:" # FIXME
        self.read()

    def read(self):
        print("Loading addressbook.")
        if os.path.isfile(self.contacts_file_name):
            self.contact_list = []
            ad_book_file = file(self.contacts_file_name, "r")
            kw_len = len(self.SELECTED_KEYNAME)
            for line in ad_book_file:
                if line[:kw_len] == self.SELECTED_KEYNAME:
                    self.selected = int(line[kw_len:].strip())
                    print("Loading selected contact: %s" % (self.selected))
                else:
                    try:
                        print("Loading contact %s" % (line.strip()))
                        d = json.loads(line)
                        for k, v in d.iteritems():
                            if type(v) is unicode:
                                v = str(v) # FIXME
                        self.contact_list.append(d)
                    except Exception, e:
                        print str(e)
            ad_book_file.close()

    def write(self):
        if ((os.path.isfile(self.contacts_file_name)) or (len(self.contact_list) > 0)):
            try:
                ad_book_file = file(self.contacts_file_name, "w")
                for contact in self.contact_list:
                    ad_book_file.write(json.dumps(contact) + "\n")
                if self.selected:
                    ad_book_file.write(self.SELECTED_KEYNAME + str(self.selected) + "\n")
                ad_book_file.close()
            except:
                print _("Cannot write Address Book file")

class Application(object):
    """
    Main application (arguably God) class
     * Contains the main GTK window
    """
    def __init__(self, kiosk_mode=False):
        self.config = Config()
        self.ad_book = AddressBook()
        self.streamer_manager = StreamerManager(self)
        self._has_session = False
        self.streamer_manager.state_changed_signal.connect(self.on_streamer_state_changed)
        print "Starting SIC server on port %s" % (self.config.negotiation_port)
        self.server = communication.Server(self, self.config.negotiation_port)
        self.client = None
        self.got_bye = False

        # Set the Glade file
        glade_file = os.path.join(PACKAGE_DATA, 'maugis.glade')
        if os.path.isfile(glade_file):
            glade_path = glade_file
        else:
            text = _("<b><big>Could not find the Glade file?</big></b>\n\n" \
                    "Be sure the file %s is in /usr/share/maugis/. Quitting.") % glade_file
            print text
            sys.exit()
        self.widgets = gtk.glade.XML(glade_path, domain=APP_NAME)
        
        # connects callbacks to widgets automatically
        cb = {}
        for n in dir(self.__class__):
            if n[0] != '_' and hasattr(self, n):
                cb[n] = getattr(self, n)
        self.widgets.signal_autoconnect(cb)

        # get all the widgets that we use
        self.main_window = self.widgets.get_widget("mainWindow")
        self.dialog = self.widgets.get_widget("normalDialog")
        self.dialog.connect('delete-event', self.dialog.hide_on_delete)
        self.dialog.set_transient_for(self.main_window)
        self.confirm_label = self.widgets.get_widget("confirmLabel")
        self.contacting_window = self.widgets.get_widget("contactingWindow")
        self.contacting_window.connect('delete-event', self.contacting_window.hide_on_delete)
        self.contact_dialog = self.widgets.get_widget("contactDialog")
        self.contact_dialog.connect('delete-event', self.contact_dialog.hide_on_delete)
        self.contact_dialog.set_transient_for(self.main_window)
        self.contact_problem_label = self.widgets.get_widget("contactProblemLabel")
        self.contact_request_dialog = self.widgets.get_widget("contactRequestDialog")
        self.contact_request_dialog.connect('delete-event', self.contact_request_dialog.hide_on_delete)
        self.contact_request_dialog.set_transient_for(self.main_window)
        self.contact_request_label = self.widgets.get_widget("contactRequestLabel")
        self.edit_contact_window = self.widgets.get_widget("editContactWindow")
        self.edit_contact_window.set_transient_for(self.main_window)
        self.contact_name_entry = self.widgets.get_widget("contactNameEntry")
        self.contact_ip_entry = self.widgets.get_widget("contactIPEntry")
        self.contact_port_entry = self.widgets.get_widget("contactPortEntry")
        self.contact_edit_but = self.widgets.get_widget("contactEditBut")
        self.remove_contact = self.widgets.get_widget("removeContact")
        self.contact_join_but = self.widgets.get_widget("contactJoinBut")
        self.info_label = self.widgets.get_widget("infoLabel")
        self.contact_list = self.widgets.get_widget("contactList")
        self.negotiation_port_entry = self.widgets.get_widget("netConfPortEntry")
        self.net_conf_bw_combo = self.widgets.get_widget("netConfBWCombo")
        # pos of currently selected contact
        self.selected_contact_row = None
        self.select_contact_num = None

        # adjust the bandwidth combobox iniline with the config 
        self.init_bandwidth()
        
        # switch to Kiosk mode if asked
        if kiosk_mode:
            self.main_window.set_decorated(False)
            self.widgets.get_widget("sysBox").show()
        
        # Build the contact list view
        self.selection = self.contact_list.get_selection()
        self.selection.connect("changed", self.on_contact_list_changed, None) 
        self.contact_tree = gtk.ListStore(str)
        self.contact_list.set_model(self.contact_tree)
        column = gtk.TreeViewColumn(_("Contacts"), gtk.CellRendererText(), markup=0)
        self.contact_list.append_column(column)
        self.init_ad_book_contact_list()
        self.init_negotiation_port()

        self.main_window.show()

        try:
            self.server.start_listening()
        except error.CannotListenError, e:
            print("Cannot start SIC server.")
            print str(e)
            raise
        reactor.addSystemEventTrigger("before", "shutdown", self.before_shutdown)
        
    def before_shutdown(self):
        print("The application is shutting down.")
        # TODO: stop streamers
        if self.client is not None:
            if not self.got_bye:
                self.send_bye()
                self.stop_streamers()
            self.disconnect_client()
        self.server.close()
        self.ad_book.write()
        
    def on_main_window_destroy(self, *args):
        reactor.stop()

    def on_main_tabs_switch_page(self, widget, notebook_page, page_number):
        tab = widget.get_nth_page(page_number)
        if tab == "localPan":
            self.widgets.get_widget("netConfSetBut").grab_default()
        elif tab == "contactPan":
            self.widgets.get_widget("contactJoinBut").grab_default()

    def on_contact_list_changed(self, *args):
        tree_list, self.selected_contact_row = args[0].get_selected()
        if self.selected_contact_row:
            self.contact_edit_but.set_sensitive(True)
            self.remove_contact.set_sensitive(True)
            self.contact_join_but.set_sensitive(True)
            self.selected_contact_num = tree_list.get_path(self.selected_contact_row)[0]
            self.ad_book.contact = self.ad_book.contact_list[self.selected_contact_num]
            self.ad_book.selected = self.selected_contact_num
        else:
            self.contact_edit_but.set_sensitive(False)
            self.remove_contact.set_sensitive(False)
            self.contact_join_but.set_sensitive(False)
            self.ad_book.contact = None

    def on_contact_list_row_activated(self, *args):
        self.on_contact_edit_but_clicked(args)

    def on_add_contact_clicked(self, *args):
        self.ad_book.new_contact = True
        self.contact_name_entry.set_text("")
        self.contact_ip_entry.set_text("")
        self.contact_port_entry.set_text("")
        self.edit_contact_window.show()

    def on_remove_contact_clicked(self, *args):
        def on_confirm_result(result):
            if result:
                del self.ad_book.contact_list[self.selected_contact_num]
                self.contact_tree.remove(self.selected_contact_row)
                self.ad_book.write()
                num = self.selected_contact_num - 1
                if num < 0:
                    num = 0
                self.selection.select_path(num)
        text = _("<b><big>Delete this contact from the list?</big></b>\n\nAre you sure you want "
            "to delete this contact from the list?")
        self.show_confirm_dialog(text, on_confirm_result)

    def on_contact_edit_but_clicked(self, *args):
        self.contact_name_entry.set_text(self.ad_book.contact["name"])
        self.contact_ip_entry.set_text(self.ad_book.contact["address"])
        self.contact_port_entry.set_text(str(self.ad_book.contact["port"]))
        self.edit_contact_window.show()

    def on_edit_contact_window_delete_event(self, *args):
        widget = args[0]
        widget.hide()
        return True

    def on_edit_contact_cancel_but_clicked(self, *args):
        self.edit_contact_window.hide()

    def on_edit_contact_save_but_clicked(self, *args):
        ad_book = self.ad_book

        def when_valid_save():
            """ Saves contact info after it's been validated and then closes the window"""
            if ad_book.new_contact:
                self.contact_tree.append([
                    "<b>" + self.contact_name_entry.get_text()
                    + "</b>\n  IP: " + addr
                    + "\n  Port: " + port])
                ad_book.contact_list.append({})
                self.selection.select_path(len(ad_book.contact_list) - 1)
                ad_book.contact = ad_book.contact_list[len(ad_book.contact_list) - 1]
                ad_book.new_contact = False
            else:
                self.contact_tree.set_value(
                    self.selected_contact_row, 0, "<b>" + 
                    self.contact_name_entry.get_text() + 
                    "</b>\n  IP: " + addr + "\n  Port: " + port)
            ad_book.contact["name"] = self.contact_name_entry.get_text()
            ad_book.contact["address"] = addr
            ad_book.contact["port"] = int(port)
            ad_book.write()
            self.edit_contact_window.hide()

        # Validate the port number
        port = self.contact_port_entry.get_text()
        if port == "":
            port = str(self.config.negotiation_port) # set port to default
        elif (not port.isdigit()) or (int(port) not in range(10000, 65535)):
            text = _("<b><big>The port number is not valid</big></b>\n\nEnter a valid port number in the range of 10000-65535")
            self.show_error_dialog(text)
            return
        # Validate the address
        addr = self.contact_ip_entry.get_text()
        if len(addr) < 7:
            text = _("<b><big>The address is not valid</big></b>\n\nEnter a valid address\nExample: 168.123.45.32 or example.org")
            self.show_error_dialog(text)
            return
        # save it.
        when_valid_save()

    def on_net_conf_set_but_clicked(self, *args):
        os.system('gksudo "network-admin"')

    def on_sys_shutdown_but_clicked(self, *args):
        def on_confirm_result(result):
            if result:
                os.system('gksudo "shutdown -h now"')

        text = _("<b><big>Shutdown the computer?</big></b>\n\nAre you sure you want to shutdown the computer now?")
        self.show_confirm_dialog(text, on_confirm_result)

    def on_sys_reboot_but_clicked(self, *args):
        def on_confirm_result(result):
            if result:
                os.system('gksudo "shutdown -r now"')

        text = _("<b><big>Reboot the computer?</big></b>\n\nAre you sure you want to reboot the computer now?")
        self.show_confirm_dialog(text, on_confirm_result)

    def on_maint_upd_but_clicked(self, *args):
        os.system('gksudo "update-manager"')

    def on_maint_send_but_clicked(self, *args):
        """ send button clicked will prompt via confirm dialog """
        def on_confirm_result(result):
            if result:
                msg = "--- milhouse_send ---\n" + self.milhouse_send_version + "\n"
                msg += "--- milhouse_recv ---\n" + self.milhouse_recv_version + "\n"
                msg += "--- uname -a ---\n"
                try:
                    w, r, err = os.popen3('uname -a')
                    msg += r.read() + "\n"
                    errRead = err.read()
                    if errRead:
                        msg += errRead + "\n"
                    w.close()
                    r.close()
                    err.close()
                except:
                    msg += "Error executing 'uname -a'\n"
                msg += "--- lsmod ---\n"
                try:
                    w, r, err = os.popen3('lsmod')
                    msg += r.read()
                    errRead = err.read()
                    if errRead:
                        msg += "\n" + errRead
                    w.close()
                    r.close()
                    err.close()
                except:
                    msg += "Error executing 'lsmod'"

                fromaddr = "maugis@sat.qc.ca"
                toaddrs  = self.config.emailinfo
                toaddrs = toaddrs.split(', ')
                server = smtplib.SMTP(self.config.smtpserver)
                server.set_debuglevel(0)
                try:
                    server.sendmail(fromaddr, toaddrs, msg)
                except:
                    text = _("<b><big>Could not send info.</big></b>\n\nCheck your internet connection.")
                    self.show_error_dialog(text)
                server.quit()

        text = _("<b><big>Send the settings?</big></b>\n\nAre you sure you want to send your computer settings to the administrator of maugis?")
        self.show_confirm_dialog(text, on_confirm_result)

    def has_session(self):
        """
        @rettype: bool
        """
        return self._has_session
        
    def on_client_join_but_clicked(self, *args):
        # XXX
        """
        Sends an INVITE to the remote peer.
        """
        msg = {
            "msg":"INVITE",
            "sid":0, 
            "videoport": self.config.recv_video_port,
            "audioport": self.config.recv_audio_port,
            "please_send_to_port": self.config.negotiation_port
            }
        port = self.config.negotiation_port # self.ad_book.contact["port"]
        ip = self.ad_book.contact["address"]

        def _on_connected(proto):
            self.client.send(msg)
            return proto
        def _on_error(reason):
            print "error trying to connect to %s:%s : %s" % (ip, port, reason)
            self.contacting_window.hide()
            return reason
           
        print "sending %s to %s:%s" % (msg, ip, port) 
        self.client = communication.Client(self, port)
        deferred = self.client.connect(ip)
        deferred.addCallback(_on_connected).addErrback(_on_error)
        self.contacting_window.show()
        # window will be hidden when we receive ACCEPT or REFUSE

    def on_net_conf_bw_combo_changed(self, *args):
        base = 30
        num = 2 # number of choice
        step = base / num
        selection = self.net_conf_bw_combo.get_active()
        self.config.bandwidth = (selection + 1) * step
        self.config._write()

    def on_net_conf_port_entry_changed(self, *args):
        # call later (we think)
        gobject.timeout_add(0, self.on_net_conf_port_entry_changed_call_later, args)
        return False

    def on_net_conf_port_entry_changed_call_later(self, *args):
        def on_error_dialog_result(result):
            self.negotiation_port_entry.grab_focus()
            return False

        port = self.negotiation_port_entry.get_text()
        if not port.isdigit():
            self.widgets.get_widget("mainTabs").set_current_page(1)
            self.init_negotiation_port()
            text = _("<b><big>The port number is not valid</big></b>\n\nEnter a valid port number in the range of 1-999999")
            self.show_error_dialog(text, on_error_dialog_result)
        else:
            self.config.negotiation_port = int(port)
            self.config._write()
            self.server.change_port(self.config.negotiation_port)

    def show_error_dialog(self, text, callback=None):
        def _response_cb(widget, response_id, callback):
            if response_id != gtk.RESPONSE_DELETE_EVENT:
                widget.hide()
            if callback is not None:
                callback()
            widget.disconnect(slot1)

        self.contact_problem_label.set_label(text)
        dialog = self.contact_dialog
        dialog.set_modal(True)
        slot1 = dialog.connect('response', _response_cb, callback)
        dialog.show()
    
    def show_confirm_dialog(self, text, callback=None):
        def _response_cb(widget, response_id, callback):
            if response_id != gtk.RESPONSE_DELETE_EVENT:
                widget.hide()
            if callback is not None:
                callback(response_id == gtk.RESPONSE_OK)
            widget.disconnect(slot1)

        self.confirm_label.set_label(text)
        dialog = self.dialog
        dialog.set_modal(True)
        slot1 = dialog.connect('response', _response_cb, callback)
        dialog.show()

    def show_contact_request_dialog(self, text, callback=None):
        """ We disconnect and reconnect the callbacks every time
            this is called, otherwise we'd would have multiple 
            callback invokations per response since the widget 
            stays alive """
        def _response_cb(widget, response_id, callback):
            if response_id != gtk.RESPONSE_DELETE_EVENT:
                widget.hide()
            if callback is not None:
                callback(response_id == gtk.RESPONSE_OK)
            widget.disconnect(slot1)

        self.contact_request_label.set_label(text)
        dialog = self.contact_request_dialog
        dialog.set_modal(True)
        slot1 = dialog.connect('response', _response_cb, callback)
        dialog.show()

    def hide_contacting_window(self, msg="", err=""):
        self.contacting_window.hide()
        text = None
        if msg == "err":
            text = _("<b><big>Contact unreacheable.</big></b>\n\nCould not connect to the IP address of this contact.")
        elif msg == "timeout":
            text = _("<b><big>Connection timeout.</big></b>\n\nCould not connect to the port of this contact.")
        elif msg == "answTimeout":
            text = _("<b><big>Contact answer timeout.</big></b>\n\nThe contact did not answer soon enough.")
        elif msg == "send":
            text = _("<b><big>Problem sending command.</big></b>\n\nError: %s") % err
        elif msg == "refuse":
            text = _("<b><big>Connection refused.</big></b>\n\nThe contact refused the connection.")
        elif msg == "badAnsw":
            text = _("<b><big>Invalid answer.</big></b>\n\nThe answer was not valid.")
        if text is not None:
            self.show_error_dialog(text)

    def init_bandwidth(self):
        base = 30
        num = 2 # number of choice
        selection = int(round((self.config.bandwidth - 1) * num / base))
        if selection < 0:
            selection = 0
        elif selection > base:
            selection = base
        self.net_conf_bw_combo.set_active(selection)

    def init_negotiation_port(self):
        self.negotiation_port_entry.set_text(str(self.config.negotiation_port))

    def init_ad_book_contact_list(self):
        ad_book = self.ad_book
        ad_book.contact = None
        ad_book.new_contact = False
        if len(ad_book.contact_list) > 0:
            for contact in ad_book.contact_list:
                self.contact_tree.append(    ["<b>" + contact["name"]
                                            + "</b>\n  IP: "
                                            + contact["address"] + "\n  Port: "
                                            + str(contact["port"])] )
            self.selection.select_path(ad_book.selected)
        else:
            self.contact_edit_but.set_sensitive(False)
            self.remove_contact.set_sensitive(False)
            self.contact_join_but.set_sensitive(False)

    def on_server_rcv_command(self, message, addr, server):
        # XXX
        msg = message["msg"]
        addr = server.get_peer_ip()
        print "Got %s from %s" % (msg, addr)
        
        if msg == "INVITE":
            # FIXME: this doesn't make sense here
            self.got_bye = False
            # TODO
            # if local user doesn't respond, close dialog in 5 seconds
            
            def _on_contact_request_dialog_result(result):
                """
                User is accetping or declining an offer.
                @param result: Answer to the dialog.
                """
                # unschedule server answer timeout
                gobject.source_remove(server_answer_timeout_watch)
                if result:
                    if self.client is not None:
                        self.client.send({"msg":"ACCEPT", "videoport":self.config.recv_video_port, "audioport":self.config.recv_audio_port, "sid":0})
                        # TODO: Use session to contain settings and ports
                        self.config.send_video_port = message["videoport"]
                        self.config.send_audio_port = message["audioport"]
                    else:
                        print "Error: connection lost, so we could not accept." # FIXME
                else:
                    if self.client is not None:
                        self.client.send({"msg":"REFUSE", "sid":0})
                return True

            # TODO: if already streaming, answer REFUSE
            send_to_port = message["please_send_to_port"]
            print "sending to %s:%s" % (addr, send_to_port)
            self.client = communication.Client(self, send_to_port)
            self.client.connect(addr)
            # user must respond in less than 5 seconds
            server_answer_timeout_watch = gobject.timeout_add(5000, self.server_answer_timeout, addr)
            text = _("<b><big>" + addr[0] + " is contacting you.</big></b>\n\nDo you accept the connection?")
            self.show_contact_request_dialog(text, _on_contact_request_dialog_result)
            # TODO: change our sending audio/video ports based on those remote told us
            
        elif msg == "ACCEPT":
            # FIXME: this doesn't make sense here
            self.got_bye = False
            # TODO: Use session to contain settings and ports
            if self.client is not None:
                self.hide_contacting_window("accept")
                self.config.send_video_port = message["videoport"]
                self.config.send_audio_port = message["audioport"]
                self.client.send({"msg":"ACK", "sid":0})
                print("Got ACCEPT. Starting streamers as initiator.")
                self.start_streamers(addr)
            else:
                print("Error ! Connection lost.") # FIXME
        elif msg == "REFUSE":
            self.hide_contacting_window("refuse")
        elif msg == "ACK":
            print("Got ACK. Starting streamers as answerer.")
            self.start_streamers(addr)
        elif msg == "BYE":
            self.got_bye = True
            self.stop_streamers()
            if self.client is not None:
                print 'disconnecting client and sending BYE'
                self.client.send({"msg":"OK", "sid":0})
                self.disconnect_client()
        elif msg == "OK":
            print "received ok. Everything has an end."
            if self.client is not None:
                print 'disconnecting client'
                self.disconnect_client()

    def start_streamers(self, addr):
        self._has_session = True
        self.streamer_manager.start(addr, self.config)

    def stop_streamers(self):
        self.streamer_manager.stop()

    def on_streamers_stopped(self, addr):
        """
        We call this when all streamers are stopped.
        """
        print "on_streamers_stopped got called"
        self._has_session = False
        
    def disconnect_client(self):
        """
        Disconnects the SIC sender.
        @rettype: L{Deferred}
        """
        def _cb(result, d1):
            self.client = None
            d1.callback(True)
        def _cl(d1):
            if self.client is not None:
                d2 = self.client.disconnect()
                d2.addCallback(_cb, d1)
            else:
                d1.callback(True)
        if self.client is not None:
            d = defer.Deferred()
            reactor.callLater(0, _cl, d)
            return d
        else: 
            return defer.succeed(True)

    def send_bye(self):
        """
        Sends BYE
        BYE stops the streaming on the remote host.
        """
        if self.client is not None:
            self.client.send({"msg":"BYE", "sid":0})

    def on_streamer_state_changed(self, streamer, new_state):
        """
        Slot for scenic.streamer.StreamerManager.state_changed_signal
        """
        if new_state in [process.STATE_STOPPED]:
            if not self.got_bye:
                """ got_bye means our peer sent us a BYE, so we shouldn't send one back """
                print("Local StreamerManager stopped. Sending BYE")
                self.send_bye()
            
    def server_answer_timeout(self, addr):
        # XXX
        self.contact_request_dialog.response(gtk.RESPONSE_NONE)
        self.contact_request_dialog.hide()
        text = _("<b><big>%s was contacting you.</big></b>\n\nBut you did not answer in reasonable delay.") % addr
        self.show_error_dialog(text)
        return False

    def on_client_socket_timeout(self, client):
        # XXX
        self.hide_contacting_window("timeout")
    
    def on_client_socket_error(self, client, err, msg):
        # XXX
        self.hide_contacting_window(msg)
        self.show_error_dialog(str(err) +": " +  str(msg))

    def on_client_connecting(self, client):
        # XXX
        """
        Slot for the sending_signal of the client.
        schedules some stuff.
        """
        # call later
        self.answ_watch = gobject.timeout_add(5000, self.client_answer_timeout, client)

    def client_answer_timeout(self, client):
        # XXX
        if self.contacting_window.get_property('visible'):
            self.hide_contacting_window("answTimeout")
    
#    def on_start_milhouse_send(self):
#        self.contact_join_but.set_sensitive(False)
#
#    def on_stop_milhouse_send(self):
#        # FIXME: what is that ?
#        self.contact_join_but.set_sensitive(True)


