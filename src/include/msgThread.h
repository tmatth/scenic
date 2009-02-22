/* msgThread.h
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

#ifndef __MSG_THREAD_H__
#define __MSG_THREAD_H__

#include "baseThread.h"
#include "mapMsg.h"

typedef QueuePair_<MapMsg> QueuePair;

/** template specialization of BaseThread with MapMsg */
class MsgThread
    : public BaseThread<MapMsg>
{

};

///Instance will register a particular MsgThread as a MapMsg handler
class MainSubscriber
    : public MapMsg::Subscriber
{
    MsgThread &t_;
    public:
        MainSubscriber(MsgThread* pt)
            : t_(*pt)
        {}

        void operator()(MapMsg& msg)
        {
            t_.getQueue().push(msg);
        }
};

#endif

