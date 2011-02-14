
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

#ifndef _LOCAL_AUDIO_H_
#define _LOCAL_AUDIO_H_

#include <tr1/memory>
#include "noncopyable.h"

class Pipeline;
class AudioSource;
class AudioSourceConfig;
class AudioLevel;
class _GstElement;

class LocalAudio : boost::noncopyable
{
    public:
        LocalAudio(Pipeline &pipeline, const std::tr1::shared_ptr<AudioSourceConfig> &sourceConfig);
        ~LocalAudio();

    private:
        Pipeline &pipeline_;
        std::tr1::shared_ptr<AudioSourceConfig> sourceConfig_;
        AudioSource *source_;
        AudioLevel *level_;
        _GstElement *fakesink_;
};

#endif // _LOCAL_AUDIO_H_

