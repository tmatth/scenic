
/* factories.h
 * Copyright (C) 2008-2009 Société des arts technologiques (SAT)
 * http://www.sat.qc.ca
 * All rights reserved.
 *
 * This file is part of [propulse]ART.
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#ifndef _PORTS_H_
#define _PORTS_H_

namespace ports {
        static const int A_PORT = 12345; // arbitrary port numbers
        static const int V_PORT = 23456;
        // FIXME: get rid of AUDIO_CAPS_PORT and VIDEO_CAPS_PORT
        static const int AUDIO_CAPS_PORT = 34567; 
        static const int VIDEO_CAPS_PORT = 45678; 
        static const int CAPS_OFFSET = 20;
}

#endif // _PORTS_H_

