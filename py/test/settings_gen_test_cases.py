#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Miville
# Copyright (C) 2008 Société des arts technologiques (SAT)
# http://www.sat.qc.ca
# All rights reserved.
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Miville is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Miville.  If not, see <http://www.gnu.org/licenses/>.

"""
Distibuted telnet system test, local file 
Usage: On local machine: trial test/dist_telnet_sys_test3.py IP_ADDRESS
You should set your env variables first. 
""" 
import unittest
import pexpect
import os
import time
import sys

import test.lib_deprecated_miville_telnet as testing

testing.VERBOSE_CLIENT = True #True
testing.VERBOSE_SERVER = False
testing.START_SERVER = False # You must start miville manually on both local and remote host.
testing.start()



class Test_Generate_Settings(testing.TelnetBaseTest):
   
    def test_01_yes(self):
        self.expectTest('pof: ', 'The default prompt is not appearing.')
    
    

    


    def _add_media_stream(self, global_setting, group, type, setting, sync, port = None):
        print "_add_media_stream %s" % str(locals())

        #add media stream        
        self.tst("settings --type stream --globalsetting %s --subgroup %s --add %s" % (global_setting, group, type), "Media stream added")         
        self.tst("settings --type stream --globalsetting %s --subgroup %s --mediastream %s01 --modify setting=%d"   % (global_setting, group, type, setting), "modified")
        self.tst("settings --type stream --globalsetting %s --subgroup %s --mediastream %s01 --modify enabled=True" % (global_setting, group, type), "modified")
        self.tst("settings --type stream --globalsetting %s --subgroup %s --mediastream %s01 --modify sync_group=\"%s\"" % (global_setting, group, type, sync), "modified")

        if port != None:
            self.tst("settings --type stream --globalsetting %s --subgroup %s --mediastream %s01 --modify port=%d"  % (global_setting, group, type, port),  "modified")        
        
    def _add_global_setting_video_rx(self, name, setting, port):
        self.tst("settings --type global --add %s" % name, "Global setting added")
        # add subgroup
        self.tst("settings --type streamsubgroup -g %s --add recv" % name, "subgroup added")
        self.tst("settings --type streamsubgroup -g %s --subgroup recv --modify enabled=True" % name,"modified")     
        self.tst("settings --type streamsubgroup -g %s --subgroup recv --modify mode='receive'" % name,  "modified" )                                                                                      
        self._add_media_stream(name, 'recv', 'video', setting , 'master', port)

    def _add_global_setting_video_tx(self, name, setting, port):
        self.tst("settings --type global --add %s" % name, "Global setting added")
        # add subgroup
        self.tst("settings --type streamsubgroup -g %s --add send" % name, "subgroup added")
        self.tst("settings --type streamsubgroup -g %s --subgroup send --modify enabled=True" % name,"modified")      
        self.tst("settings --type streamsubgroup -g %s --subgroup send --modify mode='send'" %name ,"modified")                                                                                       
        #add media stream   
        self._add_media_stream(name, 'send', 'video', setting, 'master', port )     
        
    def _add_global_setting_audio_rx(self, name, setting, port):   
        self.tst("settings --type global --add %s" % name, "Global setting added")
         # add subgroup
        
        self.tst("settings --type streamsubgroup -g %s --add recv"% name, "subgroup added")
        self.tst("settings --type streamsubgroup -g %s --subgroup recv --modify enabled=True" % name ,"modified")     
        self.tst("settings --type streamsubgroup -g %s --subgroup recv --modify mode='receive'" % name,"modified")         
        
        #add media stream     
        self._add_media_stream(name , 'recv', 'audio', setting, 'master', port )    

    def _add_global_setting_audio_tx(self, name, setting, port):
        self.tst("settings --type global --add %s" % name , "Global setting added")
        # add subgroup
        self.tst("settings --type streamsubgroup -g %s --add send" % name, "subgroup added")
        self.tst("settings --type streamsubgroup -g %s --subgroup send --modify enabled=True" % name,"modified")      
        self.tst("settings --type streamsubgroup -g %s --subgroup send --modify mode='send'" % name ,"modified")                                                                                      
        #add media streams   
        self._add_media_stream(name , 'send', 'audio', setting, 'master' ,  port)     
       
    def _add_global_setting_video_rxtx(self, name, setting_rx, setting_tx, port_rx=None, port_tx=None):        
        ###Video Two way           
        self.tst("settings --type global --add %s" % name, "Global setting added")
        # add subgroup
        self.tst("settings --type streamsubgroup -g %s --add recv" % name , "subgroup added")
        self.tst("settings --type streamsubgroup -g %s --subgroup recv --modify enabled=True" % name ,"modified")     
        self.tst("settings --type streamsubgroup -g %s --subgroup recv --modify mode='receive'" % name ,"modified")                                                                                      
        #add media stream      
        self._add_media_stream(name , 'recv', 'video', setting_rx, 'master', port_rx)   

        # add subgroup
        self.tst("settings --type streamsubgroup -g %s --add send" % name, "subgroup added")
        self.tst("settings --type streamsubgroup -g %s --subgroup send --modify enabled=True" % name,"modified")      
        self.tst("settings --type streamsubgroup -g %s --subgroup send --modify mode='send'" % name ,"modified")                                                                                       
        
        #add media stream     
        self._add_media_stream(name , 'send', 'video', setting_tx, 'master',  port_tx)    

###################################################################################

    def _add_global_setting_audio_rxtx(self, name, setting_rx, setting_tx, port_rx=None, port_tx=None):
        ###Audio Two way
        self.tst("settings --type global --add %s" % name , "Global setting added")
        # add subgroup
        self.tst("settings --type streamsubgroup -g %s --add recv" % name, "subgroup added")
        self.tst("settings --type streamsubgroup -g %s --subgroup recv --modify enabled=True" % name ,"modified")     
        self.tst("settings --type streamsubgroup -g %s --subgroup recv --modify mode='receive'" % name ,"modified")                                                                                      
        #add media stream  
        self._add_media_stream(name , 'recv', 'audio', setting_rx, 'master', port_rx )       
        # add subgroup
        self.tst("settings --type streamsubgroup -g %s --add send" % name, "subgroup added")
        self.tst("settings --type streamsubgroup -g %s --subgroup send --modify enabled=True" % name,"modified")     
        self.tst("settings --type streamsubgroup -g %s --subgroup send --modify mode='send'" %name ,"modified")                                                                                      
        #add media stream    
        self._add_media_stream(name , 'send', 'audio', setting_tx, 'master',  port_tx)     

#############################################################################################
      
    def _add_global_setting_AV_rxtx(self, name, setting_id_tx_video, setting_id_rx_video, setting_id_tx_audio, setting_id_rx_audio, port_tx_video=None, port_rx_video=None, port_tx_audio=None, port_rx_audio=None):
        
        self.tst("settings --type global --add %s" % name , "Global setting added")
       
        self.tst("settings --type streamsubgroup -g %s --add recv" % name, "subgroup added")
        self.tst("settings --type streamsubgroup -g %s --subgroup recv --modify enabled=True" %name ,"modified")     
        self.tst("settings --type streamsubgroup -g %s --subgroup recv --modify mode='receive'" % name ,"modified")                                                                                      
       
       
        self.tst("settings --type streamsubgroup -g %s --add send" % name, "subgroup added")
        self.tst("settings --type streamsubgroup -g %s --subgroup send --modify enabled=True" % name ,"modified")     
        self.tst("settings --type streamsubgroup -g %s --subgroup send --modify mode='send'" % name ,"modified")                 
        
        self._add_media_stream(name , 'recv', 'video', setting_id_rx_video, 'master', port_rx_video )   
                                                                                     
        self._add_media_stream(name , 'send', 'video', setting_id_tx_video, 'master',  port_tx_video)  
              
        self._add_media_stream(name , 'recv', 'audio', setting_id_rx_audio, 'master', port_rx_audio )   

        self._add_media_stream(name , 'send', 'audio', setting_id_tx_audio, 'master',  port_tx_audio)  
 
    def _add_global_setting_AV_rxtx_unsync(self, name, setting_id_tx_video, setting_id_rx_video, setting_id_tx_audio, setting_id_rx_audio, port_tx_video=None, port_rx_video=None, port_tx_audio=None, port_rx_audio=None):
        
        self.tst("settings --type global --add %s" % name , "Global setting added")
       
        self.tst("settings --type streamsubgroup -g %s --add recv" % name, "subgroup added")
        self.tst("settings --type streamsubgroup -g %s --subgroup recv --modify enabled=True" %name ,"modified")     
        self.tst("settings --type streamsubgroup -g %s --subgroup recv --modify mode='receive'" % name ,"modified")                                                                                      
       
       
        self.tst("settings --type streamsubgroup -g %s --add send" % name, "subgroup added")
        self.tst("settings --type streamsubgroup -g %s --subgroup send --modify enabled=True" % name ,"modified")     
        self.tst("settings --type streamsubgroup -g %s --subgroup send --modify mode='send'" % name ,"modified")                 
        
        self._add_media_stream(name , 'recv', 'video', setting_id_rx_video, 'vid', port_rx_video )   
                                                                                     
        self._add_media_stream(name , 'send', 'video', setting_id_tx_video, 'vid',  port_tx_video)  
              
        self._add_media_stream(name , 'recv', 'audio', setting_id_rx_audio, 'aud', port_rx_audio )   

        self._add_media_stream(name , 'send', 'audio', setting_id_tx_audio, 'aud',  port_tx_audio)  



    def _add_contact(self, name, address, settings): 
        port = 2222
        for i in settings:
            contact = name
            if len(settings) > 1:
                contact = '%s_%d' % (name,i)
                #port += 10
                
            self.tst("contacts --add %s %s %d" % (contact, address, port), "Contact added")
            self.tst("contacts --select %s" % contact, "Contact selected")   
            self.tst("contacts --modify port=%d" % port,"Contact modified") 
            self.tst("contacts --modify setting=%d" % i,"Contact modified")
    
    def _add_media_settings_audio_rxtx(self, name, codec, channels, source):
        self.media_settings.append("%s_tx" % name)
        self.tst("settings --type media --add %s_tx" % name, "Media setting added")
        self.tst('settings --type media --mediasetting %s_tx  --modify settings=codec:%s' % (name,codec) , 'modified')
        self.tst('settings --type media --mediasetting %s_tx  --modify settings=engine:Gst' % (name) , 'modified')
        self.tst('settings --type media --mediasetting %s_tx  --modify settings=source:%s' % (name,source)    , 'modified')       
        self.tst('settings --type media --mediasetting %s_tx  --modify settings=channels:%d' % (name, channels) , 'modified')         
            
        self.media_settings.append("%s_rx" % name)
        self.tst("settings --type media --add %s_rx" % name , "Media setting added")
        self.tst('settings --type media --mediasetting %s_rx  --modify settings=codec:%s' % (name,codec) , 'modified')    
        self.tst('settings --type media --mediasetting %s_rx  --modify settings=engine:Gst'% (name), 'modified')
        self.tst('settings --type media --mediasetting %s_rx  --modify settings=source:%s' % (name, source) , 'modified') 
        self.tst('settings --type media --mediasetting %s_rx  --modify settings=channels:%d' % (name, channels) , 'modified')
        self.tst('settings --type media --mediasetting %s_rx  --modify settings=audio_buffer_usec:30000' % (name), 'modified')              


    def _add_media_settings_video_rxtx(self, name, codec, source, bitrate):

        self.media_settings.append("%s_rx" % name)
        self.tst("settings --type media --add %s_rx" % name, "Media setting added")
        self.tst('settings --type media --mediasetting %s_rx  --modify settings=codec:%s' % (name,codec) , 'modified')
        self.tst('settings --type media --mediasetting %s_rx  --modify settings=bitrate:2048000' % name       , 'modified')
        self.tst('settings --type media --mediasetting %s_rx  --modify settings=engine:Gst'  % name          , 'modified')
        self.tst('settings --type media --mediasetting %s_rx  --modify settings=source:%s' % ( name , source)  , 'modified') 
                                                             

        self.media_settings.append("%s_tx" % name)
        self.tst("settings --type media --add %s_tx" % name, "Media setting added")
        self.tst('settings --type media --mediasetting %s_tx  --modify settings=codec:%s' % (name,codec)           , 'modified')
        self.tst('settings --type media --mediasetting %s_tx  --modify settings=bitrate:%d' % (name,bitrate)      , 'modified')
        self.tst('settings --type media --mediasetting %s_tx  --modify settings=engine:Gst'   % name         , 'modified')
        self.tst('settings --type media --mediasetting %s_tx  --modify settings=source:%s' % (name, source)   , 'modified')       
        


    def test_02_media_settings(self):
        
        #videosrc = 'v4l2src'
        videosrc = 'videotestsrc'
        
        print
        print "HOME IS: " + os.environ['HOME']
        
        self.media_settings = []
        
        self._add_media_settings_video_rxtx("video_mpeg4", "mpeg4", videosrc, 3000000 )
        self._add_media_settings_video_rxtx("video_h263", "h263", videosrc, 3000000)
        self._add_media_settings_video_rxtx("video_h264", "h264", videosrc, 3000000)        
              
        self._add_media_settings_audio_rxtx("audio_raw2", "raw", 2, "audiotestsrc")
        self._add_media_settings_audio_rxtx("audio_raw4", "raw", 4, "audiotestsrc")
        self._add_media_settings_audio_rxtx("audio_raw6", "raw", 6, "audiotestsrc")
        self._add_media_settings_audio_rxtx("audio_raw8", "raw", 8, "audiotestsrc")
        self._add_media_settings_audio_rxtx("audio_mp3", "mp3", 2, "audiotestsrc")
        self._add_media_settings_audio_rxtx("audio_vorbis2", "vorbis", 2, "audiotestsrc")
        self._add_media_settings_audio_rxtx("audio_vorbis4", "vorbis", 4, "audiotestsrc")
        self._add_media_settings_audio_rxtx("audio_vorbis6", "vorbis", 6, "audiotestsrc")
        self._add_media_settings_audio_rxtx("audio_vorbis8", "vorbis", 8, "audiotestsrc")
        

        counter = 10000
        for media in  self.media_settings:       
            print "media[%5d] %s" % (counter,media)
            counter += 1
       
        #self.add_global_settings()\
        self.add_global_settings()
        self.add_unsync_setting()
        

    def add_unsync_setting(self):
        def get_port():
            self.port += 10
            return self.port

        self.port = 9000
        
        ###################MPEG4/RAW8##################
        setting_id_tx_video = 10000 + self.media_settings.index('video_mpeg4_tx')
        setting_id_rx_video = 10000 + self.media_settings.index('video_mpeg4_rx')
        setting_id_tx_audio = 10000 + self.media_settings.index('audio_raw8_tx')
        setting_id_rx_audio = 10000 + self.media_settings.index('audio_raw8_rx')
        self._add_global_setting_AV_rxtx_unsync('mpeg4_8raw_unsync_rxtx' , setting_id_tx_video, setting_id_rx_video, setting_id_tx_audio, setting_id_rx_audio, get_port(),get_port(),get_port(),get_port())

        self.tst("settings --save -y-9999", "saved")
        
    def add_global_settings(self):
    
        
        def get_port():
            self.port += 10
            return self.port

        self.port = 9000

        #####MPEG4##########           
        setting_id = 10000 + self.media_settings.index('video_mpeg4_rx')
        self._add_global_setting_video_rx('video_mpeg4_rx', setting_id, get_port())   
        setting_id = 10000 + self.media_settings.index('video_mpeg4_tx')
        self._add_global_setting_video_tx('video_mpeg4_tx', setting_id, get_port())
        #########H263#############

        setting_id = 10000 + self.media_settings.index('video_h263_rx')
        self._add_global_setting_video_rx('video_h263_rx', setting_id, get_port())

        setting_id = 10000 + self.media_settings.index('video_h263_tx')
        self._add_global_setting_video_tx('video_h263_tx', setting_id, get_port())
        #########H264#############

        setting_id = 10000 + self.media_settings.index('video_h264_rx')
        self._add_global_setting_video_rx('video_h264_rx', setting_id, get_port())

        setting_id = 10000 + self.media_settings.index('video_h263_tx')
        self._add_global_setting_video_tx('video_h264_tx', setting_id, get_port())
                        
        ########RAW####################        
 
        setting_id = 10000 + self.media_settings.index('audio_raw2_tx')
        self._add_global_setting_audio_rx('audio_raw2_rx', setting_id, get_port())
      
        setting_id = 10000 + self.media_settings.index('audio_raw2_rx')
        self._add_global_setting_audio_tx('audio_raw2_tx', setting_id, get_port())

        setting_id = 10000 + self.media_settings.index('audio_raw4_rx')
        self._add_global_setting_audio_rx('audio_raw4_rx', setting_id, get_port())

        setting_id = 10000 + self.media_settings.index('audio_raw4_tx')
        self._add_global_setting_audio_tx('audio_raw4_tx', setting_id, get_port())

        setting_id = 10000 + self.media_settings.index('audio_raw6_rx')
        self._add_global_setting_audio_rx('audio_raw6_rx', setting_id, get_port())

        setting_id = 10000 + self.media_settings.index('audio_raw6_tx')
        self._add_global_setting_audio_tx('audio_raw6_tx', setting_id, get_port())

        setting_id = 10000 + self.media_settings.index('audio_raw8_rx')
        self._add_global_setting_audio_rx('audio_raw8_rx', setting_id, get_port())

        setting_id = 10000 + self.media_settings.index('audio_raw8_tx')
        self._add_global_setting_audio_tx('audio_raw8_tx', setting_id, get_port())
        #####################MP3############################

        setting_id = 10000 + self.media_settings.index('audio_mp3_tx')
        self._add_global_setting_audio_tx('audio_mp3_tx', setting_id, get_port())

        setting_id = 10000 + self.media_settings.index('audio_mp3_rx')
        self._add_global_setting_audio_rx('audio_mp3_rx', setting_id, get_port())
        ########################VORBIS#######################################        

        setting_id = 10000 + self.media_settings.index('audio_vorbis2_rx')
        self._add_global_setting_audio_rx('audio_vorbis2_rx', setting_id, get_port())

        setting_id = 10000 + self.media_settings.index('audio_vorbis2_tx')
        self._add_global_setting_audio_tx('audio_vorbis2_tx', setting_id, get_port())

        setting_id = 10000 + self.media_settings.index('audio_vorbis4_rx')
        self._add_global_setting_audio_rx('audio_vorbis4_rx', setting_id, get_port())

        setting_id = 10000 + self.media_settings.index('audio_vorbis4_tx')
        self._add_global_setting_audio_tx('audio_vorbis4_tx', setting_id, get_port())

        setting_id = 10000 + self.media_settings.index('audio_vorbis6_rx')
        self._add_global_setting_audio_rx('audio_vorbis6_rx', setting_id, get_port())

        setting_id = 10000 + self.media_settings.index('audio_vorbis6_tx')
        self._add_global_setting_audio_tx('audio_vorbis6_tx', setting_id, get_port())        

        setting_id = 10000 + self.media_settings.index('audio_vorbis8_rx')
        self._add_global_setting_audio_rx('audio_vorbis8_rx', setting_id, get_port())

        setting_id = 10000 + self.media_settings.index('audio_vorbis8_tx')
        self._add_global_setting_audio_tx('audio_vorbis8_tx', setting_id, get_port())
        ##########################RAW RX/TX############################################

        setting_id_tx = 10000 + self.media_settings.index('audio_raw8_tx')
        setting_id_rx = 10000 + self.media_settings.index('audio_raw8_rx')
        self._add_global_setting_audio_rxtx('audio_raw8_rxtx', setting_id_rx, setting_id_tx , get_port(), get_port())

        setting_id_tx = 10000 + self.media_settings.index('audio_raw6_tx')
        setting_id_rx = 10000 + self.media_settings.index('audio_raw6_rx')
        self._add_global_setting_audio_rxtx('audio_raw6_rxtx', setting_id_rx, setting_id_tx , get_port(), get_port())

        setting_id_tx = 10000 + self.media_settings.index('audio_raw4_tx')
        setting_id_rx = 10000 + self.media_settings.index('audio_raw4_rx')
        self._add_global_setting_audio_rxtx('audio_raw4_rxtx', setting_id_rx, setting_id_tx , get_port(), get_port())

        setting_id_tx = 10000 + self.media_settings.index('audio_raw2_tx')
        setting_id_rx = 10000 + self.media_settings.index('audio_raw2_rx')
        self._add_global_setting_audio_rxtx('audio_raw2_rxtx', setting_id_rx, setting_id_tx , get_port(), get_port())
        
        ############################MP3 RX/TX##############################

        setting_id_tx = 10000 + self.media_settings.index('audio_mp3_tx')
        setting_id_rx = 10000 + self.media_settings.index('audio_mp3_rx')
        self._add_global_setting_audio_rxtx('audio_mp3_rxtx', setting_id_rx, setting_id_tx , get_port(), get_port())

        ###########################VORBIS RX/TX############################

        setting_id_tx = 10000 + self.media_settings.index('audio_vorbis2_tx')
        setting_id_rx = 10000 + self.media_settings.index('audio_vorbis2_rx')
        self._add_global_setting_audio_rxtx('audio_vorbis2_rxtx', setting_id_rx, setting_id_tx , get_port(), get_port())

        setting_id_tx = 10000 + self.media_settings.index('audio_vorbis4_tx')
        setting_id_rx = 10000 + self.media_settings.index('audio_vorbis4_rx')
        self._add_global_setting_audio_rxtx('audio_vorbis4_rxtx', setting_id_rx, setting_id_tx , get_port(), get_port())

        setting_id_tx = 10000 + self.media_settings.index('audio_vorbis6_tx')
        setting_id_rx = 10000 + self.media_settings.index('audio_vorbis6_rx')
        self._add_global_setting_audio_rxtx('audio_vorbis6_rxtx', setting_id_rx, setting_id_tx , get_port(), get_port())

        setting_id_tx = 10000 + self.media_settings.index('audio_vorbis8_tx')
        setting_id_rx = 10000 + self.media_settings.index('audio_vorbis8_rx')
        self._add_global_setting_audio_rxtx('audio_vorbis8_rxtx', setting_id_rx, setting_id_tx , get_port(), get_port())
        
        ##############MPEG4 RX/TX######################           
        setting_id_tx_video = 10000 + self.media_settings.index('video_mpeg4_tx')
        setting_id_rx_video = 10000 + self.media_settings.index('video_mpeg4_rx')
        self._add_global_setting_video_rxtx('video_mpeg4_rxtx', setting_id_tx_video, setting_id_rx_video, get_port(), get_port())
        
        ################H263 RX/TX########################     
        setting_id_tx_video = 10000 + self.media_settings.index('video_h263_tx')
        setting_id_rx_video = 10000 + self.media_settings.index('video_h263_rx')
        self._add_global_setting_video_rxtx('video_h263_rxtx', setting_id_tx_video, setting_id_rx_video, get_port(), get_port())
        
        ################H264 RX/TX########################      
        setting_id_tx_video = 10000 + self.media_settings.index('video_h264_tx')
        setting_id_rx_video = 10000 + self.media_settings.index('video_h264_rx')
        self._add_global_setting_video_rxtx('video_h264_rxtx', setting_id_tx_video, setting_id_rx_video, get_port(), get_port())




    def atest_04_contacts(self):  
        # add a contacts
        settings = [10000]
        self._add_contact('brrr', '10.10.10.65',  settings)
        self._add_contact('tzing', '10.10.10.66', settings)
        self._add_contact('krrt', '10.10.10.64', settings)
        self._add_contact('toc', '10.10.10.169', settings) 
        self._add_contact('pow', '10.10.10.182', settings)
        self._add_contact('bloup', '10.10.10.72', settings)   
        self._add_contact('gloup', '10.10.10.73', settings)    
        self._add_contact('flush', '10.10.10.69', settings)
 
    
  



