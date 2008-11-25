// videoSource.h
// Copyright 2008 Koya Charles & Tristan Matthews //
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

#ifndef _VIDEO_SOURCE_H_
#define _VIDEO_SOURCE_H_

#include "gstLinkable.h"

#include <gst/gstclock.h>

class VideoSourceConfig;
class _GstElement;
class _GstPad;

class VideoSource
    : public GstLinkableSource
{
    public:
        ~VideoSource();
        virtual void init();

    protected:
        explicit VideoSource(const VideoSourceConfig &config)
            : config_(config), source_(0) {}

        const VideoSourceConfig &config_;
        _GstElement *source_;

    private:
        static int base_callback(GstClock *clock, GstClockTime time, GstClockID id,
                                      void *user_data);
        virtual void sub_init() = 0;
        virtual int callback() { return FALSE; }
        _GstElement *srcElement() { return source_; }
        VideoSource(const VideoSource&);     //No Copy Constructor
        VideoSource& operator=(const VideoSource&);     //No Assignment Operator
};

class VideoTestSource
    : public VideoSource
{
    public:
        explicit VideoTestSource(const VideoSourceConfig &config)
            : VideoSource(config), clockId_(0) {}

    private:
        ~VideoTestSource();
        void sub_init();
        int callback();
        void toggle_colour();

        GstClockID clockId_;
        static const int BLACK;
        static const int WHITE;

        VideoTestSource(const VideoTestSource&);     //No Copy Constructor
        VideoTestSource& operator=(const VideoTestSource&);     //No Assignment Operator
};

class VideoFileSource
    : public VideoSource
{
    public:
        explicit VideoFileSource(const VideoSourceConfig &config)
            : VideoSource(config), decoder_(0) {}
    private:
        ~VideoFileSource();
        _GstElement *srcElement() { return 0; }      // FIXME: HACK
        void sub_init();

        _GstElement *decoder_;
        static void cb_new_src_pad(_GstElement * srcElement, _GstPad * srcPad, int last,
                                   void *data);

        VideoFileSource(const VideoFileSource&);     //No Copy Constructor
        VideoFileSource& operator=(const VideoFileSource&);     //No Assignment Operator
};

class VideoDvSource
    : public VideoSource
{
    public:
        explicit VideoDvSource(const VideoSourceConfig &config) 
            : VideoSource(config), demux_(0), queue_(0), dvdec_(0), dvIsNew_(true) {}

    private:
        ~VideoDvSource();
        
        _GstElement *srcElement() { return dvdec_; }
        void init();
        void sub_init();
        static void cb_new_src_pad(_GstElement * srcElement, _GstPad * srcPad, void *data);

        _GstElement *demux_, *queue_, *dvdec_;
        bool dvIsNew_;
        VideoDvSource(const VideoDvSource&);     //No Copy Constructor
        VideoDvSource& operator=(const VideoDvSource&);     //No Assignment Operator
};

class VideoV4lSource
    : public VideoSource
{
    public:
        explicit VideoV4lSource(const VideoSourceConfig &config)
            : VideoSource(config) {}
    private:
        void sub_init();
        VideoV4lSource(const VideoV4lSource&);     //No Copy Constructor
        VideoV4lSource& operator=(const VideoV4lSource&);     //No Assignment Operator
};

#endif //_VIDEO_SOURCE_H_

