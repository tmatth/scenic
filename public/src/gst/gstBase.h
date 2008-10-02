
// gstBase.h
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

#ifndef _GST_BASE_H_
#define _GST_BASE_H_

#include <vector>

class _GstElement;
class _GstCaps;
class Pipeline;

typedef std::vector<_GstElement *>::iterator GstIter;

class GstBase
{
    public:
        virtual bool start();
        virtual bool stop();
        virtual bool init() = 0;

        bool isPlaying() const;
        static const unsigned int SAMPLE_RATE; 

    protected:

        // this initializes pipeline only once/process
        GstBase();
        const char* getElementPadCaps(_GstElement *element, const char * padName) const;
        static void checkCapsSampleRate(_GstCaps *caps);

        virtual ~GstBase();

        Pipeline & pipeline_;

    private:
        GstBase(const GstBase&);     //No Copy Constructor
        GstBase& operator=(const GstBase&);     //No Assignment Operator
        static int refCount_;
        static int sampleRate_;
};

#endif // _GST_BASE_H_

