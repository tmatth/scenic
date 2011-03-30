
// busMsgHandler.cpp
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
// Abstract interface that defines one method, handleBusMsg


#include "busMsgHandler.h"
#include "util/logWriter.h"
#include "pipeline.h"


/** 
* Abstract interface which requires its implementors to provide 
* functionality to handle messages posted on the bus. Variation on
* the Observer and Chain of Responsibility patterns.
*/

BusMsgHandler::BusMsgHandler(Pipeline *pipeline) : pipeline_(pipeline)
{
    pipeline_->subscribe(this);
}

BusMsgHandler::BusMsgHandler() : pipeline_(0)
{}

void BusMsgHandler::setPipeline(Pipeline *pipeline)
{
    if (pipeline_ == 0)
    {
        pipeline_ = pipeline;
        pipeline_->subscribe(this);
    }
    else 
        LOG_WARNING("Pipeline has already been initialized");
}

BusMsgHandler::~BusMsgHandler() 
{
    // FIXME: not clean, but at least this way if we go down out of order due to siginit
    // we don't recreate the pipeline just to remove ourselves
    if (pipeline_->isAlive())
        pipeline_->unsubscribe(this);
}

