
// gstBase.cpp
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

#include <gst/gst.h>
#include <cassert>

#include "gstBase.h"
#include "logWriter.h"

// this initializes pipeline only once/process
GstBase::GstBase() : pipeline_(Pipeline::Instance())
{
}

GstBase::~GstBase()
{
}

bool GstBase::isPlaying()
{
	return pipeline_.isPlaying();
}

void GstBase::wait_until_playing()
{
	while (!pipeline_.isPlaying())  // wait for pipeline to get rolling
		usleep(1000);
}
