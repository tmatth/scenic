/* RTSPServer.h
 * Copyright (C) 2011 Société des arts technologiques (SAT)
 * Copyright (C) 2011 Tristan Matthews
 * http://www.sat.qc.ca
 * All rights reserved.
 *
 * This file is part of Scenic.
 *
 * Scenic is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Scenic is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Scenic.  If not, see <http://www.gnu.org/licenses/>.
 *
 */
#ifndef _RTSP_SERVER_H_
#define _RTSP_SERVER_H_

namespace boost {
    namespace program_options {
        class variables_map;
    }
}

class RTSPServer
{
    public:
        RTSPServer(const boost::program_options::variables_map &options);
        void run(int timeout);
};


#endif // _RTSP_SERVER_H_

