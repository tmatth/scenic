// audioSource.cpp
// Copyright 2008 Koya Charles & Tristan Matthews
//
// This file is part of [propulse]ART.
//
// [propulse]ART is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// [propulse]ART is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with [propulse]ART.  If not, see <http://www.gnu.org/licenses/>.
//

#include <iostream>
#include <string>
#include <cassert>
#include "logWriter.h"
#include "audioSource.h"
#include "audioConfig.h"
#include "jackUtils.h"

AudioSource::AudioSource(const AudioConfig &config) : config_(config), interleave_(config),
                                                      sources_(0), aconvs_(0)
{
}

// parts of sub_init that are common to all AudioSource classes
void AudioSource::init()
{
    interleave_.init();

    for (int channelIdx = 0; channelIdx < config_.numChannels(); channelIdx++)
    {
        sources_.push_back(gst_element_factory_make(config_.source(), NULL));
        assert(sources_[channelIdx]);
        aconvs_.push_back(gst_element_factory_make("audioconvert", NULL));
        assert(aconvs_[channelIdx]);
    }

    pipeline_.add_vector(sources_);
    pipeline_.add_vector(aconvs_);

    sub_init();
    link_elements();
    link_interleave();
}



AudioSource::~AudioSource()
{
    assert(pipeline_.stop());
    pipeline_.remove_vector(aconvs_);
    pipeline_.remove_vector(sources_);
}


void AudioSource::link_elements()
{
    GstIter src, aconv;

    for (src = sources_.begin(), aconv = aconvs_.begin(); src != sources_.end(), aconv != aconvs_.end(); ++src, ++aconv)
        gst_element_link(*src, *aconv);
}

void AudioSource::link_interleave()
{
    GstIter aconv;
    for (aconv = aconvs_.begin(); aconv != aconvs_.end(); ++aconv)
        interleave_.linkInput(*aconv);
}



// defers to subclassses callback
gboolean AudioSource::base_callback(GstClock *clock, GstClockTime time, GstClockID id, gpointer user_data)
{
    return  (static_cast<AudioSource*>(user_data)->callback());
}



// toggles the frequency
gboolean AudioTestSource::callback()
{
    static const double FREQUENCY[2][8] = {{200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0},
                                    {300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0}};
    int i = 0;

    for (std::vector<GstElement*>::iterator iter = sources_.begin(); iter != sources_.end(); ++iter)
        g_object_set(G_OBJECT(*iter), "freq", FREQUENCY[offset_][i++], NULL);

    offset_ = (offset_ == 0) ? 1 : 0;     // toggle frequency

    return TRUE;
}



void AudioTestSource::sub_init()
{
    GstIter src, aconv;

    const double GAIN = 1.0 / config_.numChannels();        // so sum of tones' amplitude equals 1.0
    double frequency = 100.0;

    // is-live must be true for clocked callback to work properly
    for (src = sources_.begin(); src != sources_.end(); ++src, frequency += 100.0)
        g_object_set(G_OBJECT(*src), "volume", GAIN, "freq", frequency, "is-live", TRUE, NULL); 

    // FIXME: move to pipeline class?
    clockId_ = gst_clock_new_periodic_id(pipeline_.clock(), pipeline_.start_time(), GST_SECOND);
    gst_clock_id_wait_async(clockId_, base_callback, this);
}



AudioTestSource::~AudioTestSource()
{
    assert(pipeline_.stop());
    gst_clock_id_unschedule(clockId_);
    gst_clock_id_unref(clockId_);
}


// FIXME: detect which decoder to use based on file 
void AudioFileSource::sub_init()
{
    GstIter src, aconv, dec;

    for (int channelIdx = 0; channelIdx < config_.numChannels(); channelIdx++)
    {
        decoders_.push_back(gst_element_factory_make("decodebin", NULL));
        assert(decoders_[channelIdx]);
    }

    pipeline_.add_vector(decoders_);

    // FIXME: location should be changeable at a higher level
    int counter = 1;
    for (src = sources_.begin(); src != sources_.end(); ++src)
    {
        char filename[15];
        sprintf(filename, "audiofile%d.wav", counter++);
        g_object_set(G_OBJECT(*src), "location", filename, NULL);
    }

    for (dec = decoders_.begin(), aconv = aconvs_.begin(); dec != decoders_.end(); ++dec, ++aconv)
        g_signal_connect(*dec, "new-decoded-pad", G_CALLBACK(AudioFileSource::cb_new_src_pad), (void *) *aconv);
}



void AudioFileSource::cb_new_src_pad(GstElement * srcElement, GstPad * srcPad, gboolean last, void *data)
{
    if (gst_pad_is_linked(srcPad))
    {
        LOG("Pad is already linked.")
            return;
    }
    else if (gst_pad_get_direction(srcPad) != GST_PAD_SRC)
    {   
        LOG("Pad is not a source");
        return;
    }
  
    GstElement *sinkElement = (GstElement *) data;
    GstStructure *str;
    GstPad *sinkPad;
    GstCaps *caps;

    sinkPad = gst_element_get_static_pad(sinkElement, "sink");
    if (GST_PAD_IS_LINKED(sinkPad))
    {
        g_object_unref(sinkPad);
        return;
    }

      /* check media type */
    caps = gst_pad_get_caps(srcPad);
    str = gst_caps_get_structure(caps, 0);
    if (!g_strrstr(gst_structure_get_name(str), "audio")) {
        gst_caps_unref(caps);
        gst_object_unref(srcPad);
        return;
    }
    gst_caps_unref(caps);

    assert(gst_pad_link(srcPad, sinkPad) == GST_PAD_LINK_OK);
    gst_object_unref(sinkPad);
}



void AudioFileSource::link_elements()
{
    GstIter src, dec;
    // link source to decoders
    for (src = sources_.begin(), dec = decoders_.begin(); src != sources_.end(), dec != decoders_.end(); ++src, ++dec)
        assert(gst_element_link(*src, *dec));
}



AudioFileSource::~AudioFileSource()
{
    assert(pipeline_.stop());
    pipeline_.remove_vector(decoders_);
}



void AudioJackSource::sub_init()
{
    assert(jack_is_running());

    GstIter src, aconv;

    // turn off autoconnect to avoid Jack-killing input-output feedback loop, i.e.
    // jackOut -> jackIn -> jackOut ->jackIn.....
    for (src = sources_.begin(); src != sources_.end(); ++src)
        g_object_set(G_OBJECT(*src), "connect", 0, NULL);
}
