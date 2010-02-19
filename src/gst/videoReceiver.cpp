/* videoReceiver.cpp
 * Copyright (C) 2008-2009 Société des arts technologiques (SAT)
 * http://www.sat.qc.ca
 * All rights reserved.
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

#include "util.h"

#include "pipeline.h"
#include "mediaBase.h"
#include "gstLinkable.h"
#include "videoReceiver.h"
#include "videoScale.h"
#include "videoFlip.h"
#include "videoSink.h"
#include "codec.h"
#include "rtpPay.h"
#include "messageDispatcher.h"

#include <boost/shared_ptr.hpp>

using boost::shared_ptr;
    
VideoReceiver::VideoReceiver(Pipeline &pipeline,
        shared_ptr<VideoSinkConfig> vConfig, 
        shared_ptr<ReceiverConfig> rConfig) : 
    videoConfig_(vConfig), 
    remoteConfig_(rConfig), 
    session_(pipeline), 
    depayloader_(0), 
    decoder_(0), 
    videoscale_(0), 
    videoflip_(0), 
    sink_(0), 
    gotCaps_(false) 
{
    tassert(remoteConfig_->hasCodec()); 
    remoteConfig_->checkPorts();
    createPipeline(pipeline);
}

VideoReceiver::~VideoReceiver()
{
    remoteConfig_->cleanupPorts();
    delete sink_;
    delete videoflip_;
    delete videoscale_;
    delete depayloader_;
    delete decoder_;
}


void VideoReceiver::createCodec(Pipeline &pipeline)
{
    tassert(decoder_ = remoteConfig_->createVideoDecoder(pipeline, videoConfig_->doDeinterlace()));
}


void VideoReceiver::createDepayloader()
{
    tassert(depayloader_ = decoder_->createDepayloader());

    gstlinkable::link(*depayloader_, *decoder_);

    session_.add(depayloader_, *remoteConfig_);
}


void VideoReceiver::createSink(Pipeline &pipeline)
{
    // avoid creating the videoflip as it has a colorspace converter
    tassert(videoscale_ = videoConfig_->createVideoScale(pipeline));
    if (videoConfig_->flipMethod() != "none")
        tassert(videoflip_ = videoConfig_->createVideoFlip(pipeline));
    tassert(sink_ = videoConfig_->createSink(pipeline));

    if (remoteConfig_->jitterbufferControlEnabled())
        MessageDispatcher::sendMessage("create-control");


    gstlinkable::link(*decoder_, *videoscale_);
    if (videoflip_ != 0)
    {
        gstlinkable::link(*videoscale_, *videoflip_);
        gstlinkable::link(*videoflip_, *sink_);
    }
    else
        gstlinkable::link(*videoscale_, *sink_);

    setCaps();
    tassert(gotCaps_);
    tassert(remoteConfig_->capsMatchCodec()); 
    decoder_->adjustJitterBuffer(); // increase jitterbuffer as needed
}

/// Used to set this VideoReceiver's RtpReceiver's caps 
void VideoReceiver::setCaps() 
{ 
    session_.setCaps(remoteConfig_->caps()); 
    gotCaps_ = true;
}
