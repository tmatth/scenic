
// audioReceiver.cpp
// Copyright 2008 Koya Charles Tristan Matthews
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

#include <sstream>
#include <cassert>

#include "logWriter.h"

#include "gstLinkable.h"
#include "audioReceiver.h"
#include "audioConfig.h"
#include "remoteConfig.h"
#include "rtpPay.h"
#include "codec.h"
#include "audioSink.h"
#include "hostIP.h"
#include <cassert>


AudioReceiver::~AudioReceiver()
{
    stop();
    delete sink_;
    delete decoder_;
    delete depayloader_;
}


void AudioReceiver::init_codec()
{
    assert(decoder_ = remoteConfig_.createDecoder());
    decoder_->init();
}


void AudioReceiver::init_depayloader()
{
    assert(depayloader_ = decoder_->createDepayloader());
    depayloader_->init();
    GstLinkable::link(*depayloader_, *decoder_);
    session_.add(depayloader_, remoteConfig_);

    init_level();
}


void AudioReceiver::init_level()
{
    level_.init();
    GstLinkable::link(*decoder_, level_);
}


void AudioReceiver::init_sink()
{
    assert(sink_ = audioConfig_.createSink());
    sink_->init();
    GstLinkable::link(level_, *sink_);   
}


void AudioReceiver::start()
{
    // CAPS MUST be set first
    set_caps(remoteConfig_.caps());
    assert(gotCaps_);
    LOG_DEBUG("Receiving audio on port " << remoteConfig_.port() << " from host " << remoteConfig_.remoteHost());
    GstBase::start();
}

        
void AudioReceiver::set_caps(const char *caps) 
{ 
    session_.set_caps(caps); 
    session_.checkSampleRate();
    gotCaps_ = true;
}

