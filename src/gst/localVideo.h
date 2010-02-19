
// localVideo.h
// Copyright (C) 2008-2009 Société des arts technologiques (SAT)
// http://www.sat.qc.ca
// All rights reserved.
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

#ifndef _LOCAL_VIDEO_H_
#define _LOCAL_VIDEO_H_

#include "videoConfig.h"
#include "noncopyable.h"

#include <boost/shared_ptr.hpp>

class VideoSource;
class VideoScale;
class VideoFlip;
class VideoSink;
class _GstElement;

class LocalVideo : public boost::noncopyable
{
    public:
        LocalVideo(Pipeline &pipeline, boost::shared_ptr<VideoSourceConfig> sourceConfig,
                boost::shared_ptr<VideoSinkConfig> sinkConfig);
        ~LocalVideo();

    private:
        Pipeline &pipeline_;
        boost::shared_ptr<VideoSourceConfig> sourceConfig_;
        boost::shared_ptr<VideoSinkConfig> sinkConfig_;
        VideoSource *source_;
        _GstElement *colourspace_;
        VideoScale *videoscale_;
        VideoFlip *videoflip_;
        VideoSink *sink_;
};

#endif // _LOCAL_VIDEO_H_
