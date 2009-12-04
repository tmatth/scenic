
/* videoScale.h
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

#ifndef _VIDEO_SCALE_H_
#define _VIDEO_SCALE_H_

#include "gstLinkable.h"

// forward declarations
class _GstElement;

/** 
 *  A filter that scales video to a specified resolution.
 */

class VideoScale : public GstLinkableFilter
{
    public:
        VideoScale(int width, int height);
        ~VideoScale();

    private:
        _GstElement *sinkElement() { return videoscale_; }
        _GstElement *srcElement() { return capsfilter_; }

        _GstElement *videoscale_;
        _GstElement *capsfilter_;

        VideoScale(const VideoScale&);     //No Copy Constructor
        VideoScale& operator=(const VideoScale&);     //No Assignment Operator
};

#endif //_VIDEO_SCALE_H_

