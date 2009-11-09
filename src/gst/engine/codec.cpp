/* codec.cpp
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

#include <algorithm> // for std::find
#include <unistd.h>

#include <gst/gst.h>
#include <gst/audio/multichannel.h>

#include "util.h"

#include <boost/thread/thread.hpp>
#include <boost/lexical_cast.hpp>

#include "codec.h"
#include "rtpPay.h"
#include "pipeline.h"
#include "mapMsg.h"

#include "rtpReceiver.h"

/// Constructor 
Encoder::Encoder() : encoder_(0)
{}


/// Destructor 
Encoder::~Encoder()
{
    Pipeline::Instance()->remove(&encoder_);
}

/// Returns bitrate property for this encoder
int Encoder::getBitrate() const
{
    tassert(encoder_);
    int bitrate; 
    g_object_get(G_OBJECT(encoder_), "bitrate", &bitrate, NULL);
    return bitrate;
}

/// Sets bitrate property for this encoder
void Encoder::setBitrate(int bitrate)
{
    tassert(encoder_);
    // if pipeline is playing, we need to set it to ready to make 
    // the bitrate change actually take effect
    if (Pipeline::Instance()->isPlaying())
    {
        Pipeline::Instance()->makeReady();
        g_object_set(G_OBJECT(encoder_), "bitrate", bitrate, NULL);
        Pipeline::Instance()->start();
    }
    else
    {
        LOG_DEBUG("SETTING BITRATE TO " << bitrate);
        g_object_set(G_OBJECT(encoder_), "bitrate", bitrate, NULL);
    }
}

/// Posts bitrate using MapMsg
void Encoder::postBitrate()
{
    tassert(encoder_);
    MapMsg mapMsg("bitrate");
    mapMsg["value"] = 
        std::string(gst_element_factory_get_longname(gst_element_get_factory(encoder_))) 
        + ": " +  boost::lexical_cast<std::string>(getBitrate());
    mapMsg.post();
}


/// Constructor 
Decoder::Decoder() : decoder_(0)
{}


/// Destructor 
Decoder::~Decoder()
{
    Pipeline::Instance()->remove(&decoder_);
}


/// Constructor 
AudioConvertedEncoder::AudioConvertedEncoder() : 
    aconv_(0) 
{}

void AudioConvertedEncoder::init()
{
    aconv_ = Pipeline::Instance()->makeElement("audioconvert", NULL);
}

/// Destructor 
AudioConvertedEncoder::~AudioConvertedEncoder()
{
    Pipeline::Instance()->remove(&aconv_);
}


/// Constructor 
AudioConvertedDecoder::AudioConvertedDecoder() : 
    aconv_(0) 
{}


void AudioConvertedDecoder::init()
{
    aconv_ = Pipeline::Instance()->makeElement("audioconvert", NULL);
}

/// Destructor 
AudioConvertedDecoder::~AudioConvertedDecoder()
{
    Pipeline::Instance()->remove(&aconv_);
}

VideoEncoder::VideoEncoder() :
    colorspc_(0), supportsInterlaced_(false)  // most codecs don't have this property
{}


/// Destructor 
VideoEncoder::~VideoEncoder()
{
    Pipeline::Instance()->remove(&colorspc_);
}


void VideoEncoder::init()
{
    tassert(encoder_ != 0);
    colorspc_ = Pipeline::Instance()->makeElement("ffmpegcolorspace", NULL); 

    if (supportsInterlaced_)  // not all encoders have this property
        g_object_set(encoder_, "interlaced", TRUE, NULL); // true if we are going to encode interlaced material

    gstlinkable::link(colorspc_, encoder_);
}


VideoDecoder::VideoDecoder() : doDeinterlace_(false), colorspc_(0), deinterlace_(0)//, queue_(0)
{}


/// Destructor 
VideoDecoder::~VideoDecoder()
{
    Pipeline::Instance()->remove(&colorspc_);
    Pipeline::Instance()->remove(&deinterlace_);
    //Pipeline::Instance()->remove(&queue_);
}


/// Sets up either decoder->queue->colorspace->deinterlace
/// or just decoder->queue
void VideoDecoder::init()
{
    // FIXME: should be settable
    enum {ALL = 0, TOP, BOTTOM}; // deinterlace produces all fields, or top, bottom

    tassert(decoder_ != 0);
#if 0
    queue_ = Pipeline::Instance()->makeElement("queue", NULL);
    g_object_set(queue_, "max-size-buffers", MAX_QUEUE_BUFFERS, NULL);
    g_object_set(queue_, "max-size-bytes", 0, NULL);
    g_object_set(queue_, "max-size-time", 0LL, NULL);
#endif
    if (doDeinterlace_)
    {
        colorspc_ = Pipeline::Instance()->makeElement("ffmpegcolorspace", NULL); 
        LOG_DEBUG("DO THE DEINTERLACE");
        deinterlace_ = Pipeline::Instance()->makeElement("deinterlace", NULL);
        g_object_set(deinterlace_, "fields", TOP, NULL);
        gstlinkable::link(decoder_, colorspc_);
        gstlinkable::link(colorspc_, deinterlace_);
     //   gstlinkable::link(deinterlace_, queue_);
    }
    //else
      //  gstlinkable::link(decoder_, queue_);

}


/// Increase jitterbuffer size
void VideoDecoder::adjustJitterBuffer() 
{
    if (doDeinterlace_)
        RtpReceiver::setLatency(LONGER_JITTER_BUFFER_MS);
}



/// Constructor 
H264Encoder::H264Encoder(MapMsg &settings) : bitrate_(settings["bitrate"]) {}


/// Destructor 
H264Encoder::~H264Encoder()
{}

// POSIX specific hardware thread info 
// http://stackoverflow.com/questions/150355/programmatically-find-the-number-of-cores-on-a-machine
// int numThreads = sysconf(_SC_NPROCESSORS_ONLN);

void H264Encoder::init()
{
    encoder_ = Pipeline::Instance()->makeElement("x264enc", NULL);
    supportsInterlaced_ = true;

    // hardware threads: 1-n, 0 for automatic 
    int numThreads = boost::thread::hardware_concurrency();

    // numthreads should be 2 or 1.
    if (numThreads > 3) // don't hog all the cores
        numThreads = 3;
    else if (numThreads == 0)
        numThreads = 1;

//    LOG_DEBUG("Using " << numThreads << " threads");
    g_object_set(encoder_, "threads", numThreads, NULL);
    // See gst-plugins-good/tests/examples/rtp/*h264*.sh
    g_object_set(encoder_, "byte-stream", TRUE, NULL);  

    // subme: subpixel motion estimation 1=fast, 6=best
    VideoEncoder::init();

    setBitrate(bitrate_);
}


void Encoder::setBitrateInKbs(int newBitrate)
{
    static const double KB_PER_BIT = 0.001;
    Encoder::setBitrate(newBitrate * KB_PER_BIT);
}

/// Overridden to convert from bit/s to kbit/s
void H264Encoder::setBitrate(int newBitrate)
{
    setBitrateInKbs(newBitrate);
}


/// Creates an h.264 rtp payloader 
Payloader* H264Encoder::createPayloader() const
{
    return new H264Payloader();
}


void H264Decoder::init()
{
    decoder_ = Pipeline::Instance()->makeElement("ffdec_h264", NULL);
    VideoDecoder::init();
}


/// Creates an h.264 RtpDepayloader 
RtpPay* H264Decoder::createDepayloader() const
{
    return new H264Depayloader();
}


/// Increase jitterbuffer size
void H264Decoder::adjustJitterBuffer() 
{
    RtpReceiver::setLatency(LONGER_JITTER_BUFFER_MS);
}



/// Constructor 
H263Encoder::H263Encoder(MapMsg &settings) : bitrate_(settings["bitrate"])
{}


/// Destructor 
H263Encoder::~H263Encoder()
{}


void H263Encoder::init()
{
    encoder_ = Pipeline::Instance()->makeElement("ffenc_h263p", NULL);    // replaced with newer version
    VideoEncoder::init();
    setBitrate(bitrate_);
}


/// Creates an h.263 rtp payloader 
Payloader* H263Encoder::createPayloader() const
{
    return new H263Payloader();
}


void H263Decoder::init()
{
    decoder_ = Pipeline::Instance()->makeElement("ffdec_h263", NULL);
    VideoDecoder::init();
}


/// Creates an h.263 RtpDepayloader 
RtpPay* H263Decoder::createDepayloader() const
{
    return new H263Depayloader();
}


/// Constructor 
Mpeg4Encoder::Mpeg4Encoder(MapMsg &settings) : bitrate_(settings["bitrate"])
{}


/// Destructor 
Mpeg4Encoder::~Mpeg4Encoder()
{}

void Mpeg4Encoder::init()
{
    encoder_ = Pipeline::Instance()->makeElement("ffenc_mpeg4", NULL);
    //supportsInterlaced_ = true; this may cause stuttering
    VideoEncoder::init();
    setBitrate(bitrate_);
}


/// Creates an h.264 rtp payloader 
Payloader* Mpeg4Encoder::createPayloader() const
{
    return new Mpeg4Payloader();
}


void Mpeg4Decoder::init()
{
    decoder_ = Pipeline::Instance()->makeElement("ffdec_mpeg4", NULL);
    VideoDecoder::init();
}


/// Creates an mpeg4 RtpDepayloader 
RtpPay* Mpeg4Decoder::createDepayloader() const
{
    return new Mpeg4Depayloader();
}


/// Constructor 
TheoraEncoder::TheoraEncoder(MapMsg &settings) : bitrate_(settings["bitrate"]), quality_(settings["quality"]) {}


/// Destructor 
TheoraEncoder::~TheoraEncoder()
{}

void TheoraEncoder::init()
{
    encoder_ = Pipeline::Instance()->makeElement("theoraenc", NULL);
    setSpeedLevel(MAX_SPEED_LEVEL);
    VideoEncoder::init();
    if (bitrate_)
        setBitrate(bitrate_);
    else
        setQuality(quality_);
}


/// Overridden to convert from bit/s to kbit/s
void TheoraEncoder::setBitrate(int newBitrate)
{
    LOG_DEBUG("Bitrate " << newBitrate);
    Encoder::setBitrateInKbs(newBitrate);
}


// theora specific
void TheoraEncoder::setQuality(int quality)
{
    tassert(encoder_ != 0);
    if (quality < MIN_QUALITY or quality > MAX_QUALITY)
        THROW_ERROR("Quality must be in range [" << MIN_QUALITY << "-" << MAX_QUALITY << "]");
    LOG_DEBUG("Quality " << quality);
    g_object_set(encoder_, "quality", quality, NULL);
}


// theora specific
void TheoraEncoder::setSpeedLevel(int speedLevel)
{
    tassert(encoder_ != 0);
    if (speedLevel < MIN_SPEED_LEVEL or speedLevel > MAX_SPEED_LEVEL)
        THROW_ERROR("Speed-level must be in range [" << MIN_SPEED_LEVEL << "-" << MAX_SPEED_LEVEL << "]");
    g_object_set(encoder_, "speed-level", speedLevel, NULL);
}



Payloader* TheoraEncoder::createPayloader() const
{
    return new TheoraPayloader();
}


void TheoraDecoder::init()
{
    decoder_ = Pipeline::Instance()->makeElement("theoradec", NULL);
    VideoDecoder::init();
}

RtpPay* TheoraDecoder::createDepayloader() const
{
    return new TheoraDepayloader();
}

/// Constructor 
VorbisEncoder::VorbisEncoder() 
{}


/// Destructor 
VorbisEncoder::~VorbisEncoder() 
{}

void VorbisEncoder::init()
{
    //AudioConvertedEncoder::init();
    encoder_ = Pipeline::Instance()->makeElement("vorbisenc", NULL);
    //gstlinkable::link(aconv_, encoder_);
}


/// Creates an RtpVorbisPayloader 
Payloader* VorbisEncoder::createPayloader() const
{
    return new VorbisPayloader();
}


unsigned long long VorbisDecoder::minimumBufferTime()
{
    return MIN_BUFFER_USEC;
}

void VorbisDecoder::init()
{
    decoder_ = Pipeline::Instance()->makeElement("vorbisdec", NULL);
}

/// Creates an RtpVorbisDepayloader 
RtpPay* VorbisDecoder::createDepayloader() const
{
    return new VorbisDepayloader();
}

/// Constructor
RawEncoder::RawEncoder()
{}


void RawEncoder::init()
{
    // FIXME: HACK ATTACK: it's simpler to have this placeholder element
    // that pretends to be an aconv, and it has no
    // effect, but this isn't very smart.
    aconv_ = Pipeline::Instance()->makeElement("audioconvert", NULL);
    //g_object_set(aconv_, "silent", TRUE, NULL);
}

/// Creates an RtpL16Payloader 
Payloader* RawEncoder::createPayloader() const
{
    return new L16Payloader();
}

/// Constructor
RawDecoder::RawDecoder()
{}


/// Creates an RtpL16Depayloader 
RtpPay* RawDecoder::createDepayloader() const
{
    return new L16Depayloader();
}

/// Constructor
LameEncoder::LameEncoder() : mp3parse_(0)
{}


/// Destructor
LameEncoder::~LameEncoder()
{
    Pipeline::Instance()->remove(&mp3parse_);
}

void LameEncoder::init()
{
    AudioConvertedEncoder::init();
    encoder_ = Pipeline::Instance()->makeElement("lamemp3enc", NULL);
    mp3parse_ = Pipeline::Instance()->makeElement("mp3parse", NULL);
    gstlinkable::link(aconv_, encoder_);
    gstlinkable::link(encoder_, mp3parse_);
}

/// Constructor
MadDecoder::MadDecoder()
{}


void MadDecoder::init()
{
    AudioConvertedDecoder::init();
    decoder_ = Pipeline::Instance()->makeElement("mad", NULL);
    gstlinkable::link(decoder_, aconv_);
}

/** 
 * Creates an RtpMpaPayloader */
Payloader* LameEncoder::createPayloader() const
{
    return new MpaPayloader();
}

/// Creates an RtpMpaDepayloader 
RtpPay* MadDecoder::createDepayloader() const
{
    return new MpaDepayloader();
}

