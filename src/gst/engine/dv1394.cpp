/* dv1394.cpp
 * Copyright 2008 Koya Charles & Tristan Matthews 
 *
 * This file is part of [propulse]ART.
 *
 * [propulse]ART is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * [propulse]ART is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with [propulse]ART.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#include "dv1394.h"
#include "raw1394Util.h"
#include "pipeline.h"
#include "util.h"

Dv1394 *Dv1394::instance_ = 0;

Dv1394::~Dv1394()
{
    Pipeline::Instance()->remove(&dvdemux_);
    Pipeline::Instance()->remove(&dv1394src_);
}


Dv1394 * Dv1394::Instance()
{
    if (instance_ == 0) {
        instance_ = new Dv1394();
        instance_->init();
    }
    return instance_;
}


void Dv1394::init()
{
    if (!Raw1394::cameraIsReady())
        THROW_ERROR("Camera is not ready");

    dv1394src_ = Pipeline::Instance()->makeElement("dv1394src", NULL);
    dvdemux_ = Pipeline::Instance()->makeElement("dvdemux", "demux");
    gstlinkable::link(dv1394src_, dvdemux_);

    // register connection callback for demux
    g_signal_connect(dvdemux_, "pad-added",
            G_CALLBACK(Dv1394::cb_new_src_pad),
            NULL);
}


void Dv1394::reset()
{
    if (instance_)
    {
        LOG_DEBUG("Dv1394 is being reset.");
        instance_->unsetAudioSink();
        instance_->unsetVideoSink();
        delete instance_;
        instance_ = 0;
    }
}


void Dv1394::setAudioSink(GstElement *audioSink)
{
    assert(audioSink);
    audioSink_ = audioSink;
}


void Dv1394::setVideoSink(GstElement *videoSink)
{
    assert(videoSink);
    videoSink_ = videoSink;
}


void Dv1394::unsetVideoSink()
{
    videoSink_  = 0;
}


void Dv1394::unsetAudioSink()
{
    audioSink_  = 0;
}



/// Called due to incoming dv stream, either video or audio, links appropriately
void Dv1394::cb_new_src_pad(GstElement *  /*srcElement*/, GstPad * srcPad, void * /*data */)
{
    GstElement *sinkElement;

    if (std::string("video") == gst_pad_get_name(srcPad))
    {
        LOG_DEBUG("Got video stream from DV");
        assert(Instance()->videoSink_);
        sinkElement = Instance()->videoSink_;
    }
    else if (std::string("audio") == gst_pad_get_name(srcPad))
    {
        LOG_DEBUG("Got audio stream from DV");
        assert(Instance()->audioSink_);
        sinkElement = Instance()->audioSink_;
    }
    else {
        LOG_DEBUG("Ignoring unknown stream from DV");
        return;
    }

    GstPad *sinkPad;

    sinkPad = gst_element_get_static_pad(sinkElement, "sink");

    if (GST_PAD_IS_LINKED(sinkPad))
    {
        g_object_unref(sinkPad);        // don't link more than once
        return;
    }
    LOG_DEBUG("Dv1394: linking new srcpad to sinkpad.");
    assert(gstlinkable::link_pads(srcPad, sinkPad));
    gst_object_unref(sinkPad);
}

