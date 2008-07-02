// 
// videoConfig.cpp
//
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

/** \file 
 *      Class for video parameter objects.
 *
 */

#include <string>
#include "videoConfig.h"

VideoConfig::VideoConfig(std::string source, std::string codec, std::string remoteHost, int port):MediaConfig(source, codec, remoteHost, port)
                                                // for sender (remote)
{
    // empty
}

VideoConfig::VideoConfig(std::string source):MediaConfig(source)
                                // for sender (local)
{
    // empty
}

VideoConfig::VideoConfig(std::string codec, int port)   // for receiver
:MediaConfig(codec, port)
{
    // empty
}

const bool VideoConfig::has_dv() const
{
    return !source_.compare("dv1394src");
}

const bool VideoConfig::has_h264() const
{
    return !codec_.compare("h264");
}
