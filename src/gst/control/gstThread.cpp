/* gstThread.cpp
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

#include "engine/mediaBase.h"
#include "gstThread.h"
#include "gstSenderThread.h"
#include "engine/playback.h"

#include <boost/bind.hpp>
#include <boost/function.hpp>

#if 0
std::string stored_ip[2];
int stored_ports[2];
int 
#endif
boost::function<void (std::string)> ff[2];
void GstThread::stop(MapMsg& ){ playback::stop();} 
void GstThread::start(MapMsg&)
{
    playback::start();
}

void GstSenderThread::start(MapMsg& )
{ 
    playback::start();
    if(ff[0])
        ff[0](video_->getCaps());
    if(ff[1])
        ff[1](audio_->getCaps());
} 
int GstThread::main()
{
    bool done = false;
    bool flipflop = false;
    while(!done)
    {
        if(g_main_context_iteration(NULL, FALSE))
            continue;
        //std::cout << (flipflop ? "-\r" : " \r");
        flipflop = !flipflop;
        //std::cout.flush();
        MapMsg f = queue_.timed_pop(100000);

        if(!f.cmd().empty())
        {
            std::string s( f.cmd());

            if(s == "quit")
            {
                queue_.push(f);
                done = true;
            }
            else if(s == "audio_init")
            {
                audio_start(f);
            }
            else if(s == "stop")
            {
                stop(f);
            }
            else if(s == "start")
            {
                start(f);
            }
            else if(s == "video_init")
            {
                video_start(f);
            }
            else if(s == "levels")
            {
                queue_.push(f);
            }
            else
                LOG_WARNING("Unknown Command.");
        }
    }

    return 0;
}


#include "util.h"

#include "gstReceiverThread.h"
#include "gstSenderThread.h"

#include "gst/videoFactory.h"
#include "gst/audioFactory.h"

GstReceiverThread::~GstReceiverThread()
{
    delete video_;
    delete audio_;
}

bool GstReceiverThread::video_start(MapMsg& msg)
{
    delete video_;
    video_ = 0;
 
    try
    {
        LOG_INFO("video_start");
        const int SCREEN_NUM = 0;
        const char *VIDEO_SINK = "xvimagesink";
        video_ = videofactory::buildVideoReceiver_(msg["address"], msg["codec"], msg["port"], SCREEN_NUM, VIDEO_SINK);
//        queue_.push(MapMsg("video_started"));
        return true;
    }
    catch(Except e)
    {
        LOG_WARNING(e.msg_);
        delete video_;
        video_ = 0;
        return false;
    }
}


bool GstReceiverThread::audio_start(MapMsg& msg)
{
    delete audio_;
    audio_ = 0;

    try
    {
        const char *AUDIO_SINK = "jackaudiosink";
        audio_ = audiofactory::buildAudioReceiver_(msg["address"], msg["codec"], msg["port"], AUDIO_SINK);
//        queue_.push(MapMsg("audio_started"));
        return true;
    }
    catch(Except e)
    {
        LOG_WARNING(e.msg_);
        delete audio_;
        audio_ = 0;
        return false;
    }
}




GstSenderThread::~GstSenderThread()
{
    delete video_;
    delete audio_;
}

bool GstSenderThread::video_start(MapMsg& msg)
{
    delete video_;
    video_ = 0;
    VideoSender* sender;
    try
    {
        //VideoSourceConfig config("dv1394src");
        //SenderConfig rConfig(msg["codec"], msg["address"], msg["port"]);
        LOG_INFO("video_start");
        const std::string VIDEO_DEVICE = "";
        bool DO_DEINTERLACE = false;

        if(msg["location"].empty())
        {
            VideoSourceConfig config(msg["source"], msg["bitrate"], VIDEO_DEVICE, DO_DEINTERLACE);
            video_ = sender = videofactory::buildVideoSender_(config, msg["address"], msg["codec"], msg["port"]);
        }
        else
        {
            VideoSourceConfig config(msg["source"], msg["bitrate"], std::string(msg["location"]), DO_DEINTERLACE);
            video_ = sender = videofactory::buildVideoSender_(config, msg["address"], msg["codec"], msg["port"]);
        }

        ff[0] = boost::bind(tcpSendBuffer,msg["address"], ports::VIDEO_CAPS_PORT, videofactory::MSG_ID, _1);
        //sender->getCaps());
//        ff[0]();
        return true;
    }
    catch(Except e)
    {
        LOG_WARNING(e.msg_);
        delete video_;
        video_ = 0;
        return false;
    }
}


bool GstSenderThread::audio_start(MapMsg& msg)
{
    delete audio_;
    audio_ = 0;
    try
    {
        AudioSender* asender;

//        SenderConfig rConfig(msg["codec"], msg["address"], msg["port"]);
        if(msg["location"].empty())
        {
            AudioSourceConfig config(msg["source"], msg["channels"]);
            audio_ = asender = audiofactory::buildAudioSender_(config, msg["address"], msg["codec"], msg["port"]);
        }
        else
        {
            AudioSourceConfig config(msg["source"], msg["location"], msg["channels"]);
            audio_ = asender = audiofactory::buildAudioSender_(config, msg["address"], msg["codec"], msg["port"]);
        }
        ff[1] = boost::bind(tcpSendBuffer,msg["address"], ports::AUDIO_CAPS_PORT, audiofactory::MSG_ID, _1);
        //Build Caps Msg
 //       MapMsg caps("caps");
 //       caps["caps_str"] = asender->getCaps();
        //Forward to tcp
 //       queue_.push(caps);
        return true;
    }
    catch(Except e)
    {
        LOG_WARNING(e.msg_);
        delete audio_;
        audio_ = 0;
        return false;
    }
}


