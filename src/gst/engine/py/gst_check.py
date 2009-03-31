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
#

""" Checks this host to ensure all gstreamer plugins needed by milhouse
are installed """

import sys

try:
    import pygst
    pygst.require('0.10')
    import gst
except ImportError:
    print "import failed, please install gst-python"
    sys.exit(0)

GST_PLUGINS = [
            'level', 
            'audioconvert', 
            'alsasink', 
            'pulsesink', 
            'decodebin', 
            'capsfilter', 
            'dvdemux', 
            'queue', 
            'ffmpegcolorspace', 
            'x264enc', 
            'ffdec_h264', 
            'ffdec_h263', 
            'ffenc_h263', 
            'ffenc_mpeg4', 
            'ffdec_mpeg4', 
            'vorbisenc', 
            'vorbisdec', 
            'lame', 
            'mad', 
            'glupload',
            'glimagesink', 
            'interleave', 
            'gstrtpbin', 
            'rtph264pay', 
            'rtph264depay', 
            'rtph263pay', 
            'rtph263depay', 
            'rtpmp4vpay', 
            'rtpmp4vdepay', 
            'rtpL16pay', 
            'rtpL16depay', 
            'rtpmpapay', 
            'rtpmpadepay', 
            'udpsrc', 
            'udpsink', 
            'xvimagesink', 
            'ximagesink', 
            'dvdec', 
            'audiotestsrc', 
            'filesrc', 
            'alsasrc', 
            'jackaudiosrc', 
            'dv1394src', 
            'pulsesrc', 
            'jackaudiosink', 
            'alsasink', 
            'pulsesink', 
            'videotestsrc', 
            'v4l2src', 
            'rtpvorbispay', 
            'rtpvorbisdepay', 
            'deinterlace2'
            ]

MISSING_PLUGINS = []

for plug in GST_PLUGINS:
    if gst.element_factory_find(plug) is None: 
        print "Error: plugin " + plug + " is NOT installed"
        MISSING_PLUGINS.append(plug)
    else:
        print plug + " installed"

print "-------------------------------"
if MISSING_PLUGINS == []:
    print "All necessary plugins installed"
else:
    print "The following gstreamer plugins need to be installed: "
    for plug in MISSING_PLUGINS:
        print plug
    print "You may have to install the corresponding development headers \
    (i.e. lib<MODULE>-dev)" 
    print "before building the missing gstreamer plugins"
        