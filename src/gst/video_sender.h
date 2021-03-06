
// Copyright (C) 2008-2009 Société des arts technologiques (SAT)
// http://www.sat.qc.ca
// All rights reserved.
//
// This file is part of Scenic.
//
// Scenic is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Scenic is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Scenic.  If not, see <http://www.gnu.org/licenses/>.
//

/** @file
 * The VideoSender component.
 * Creates and links a "videosource ! encoder ! payloader" pipeline and adds it
 * to an RTP session.
 */

#ifndef _VIDEO_SENDER_H_
#define _VIDEO_SENDER_H_

#include "media_base.h"
#include "rtp_sender.h"

#include "noncopyable.h"

#include <tr1/memory>

class VideoSourceConfig;
class VideoSource;
class VideoEncoder;
class Pay;

class VideoSender
    : public SenderBase, private boost::noncopyable
{
    public:
        VideoSender(Pipeline &pipeline,
                const std::tr1::shared_ptr<VideoSourceConfig> &vConfig,
                const std::tr1::shared_ptr<SenderConfig> &rConfig);
        ~VideoSender();

    private:
        void createSource(Pipeline &pipeline);
        void createCodec(Pipeline &pipeline);
        void createPayloader();

        std::tr1::shared_ptr<VideoSourceConfig> videoConfig_;
        RtpSender session_;
        std::tr1::shared_ptr<VideoSource> source_;
        std::tr1::shared_ptr<VideoEncoder> encoder_;
        std::tr1::shared_ptr<Pay> payloader_;
};

#endif

