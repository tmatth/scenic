// fileSource.h
// Copyright (C) 2008-2009 Société des arts technologiques (SAT)
// http://www.sat.qc.ca
// All rights reserved.
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

#ifndef _FILE_SOURCE_H_
#define _FILE_SOURCE_H_

#include <map>
#include <string>

class _GstElement;
class _GstPad;

class FileSource
{
    public:
        enum MEDIA_TYPE {VIDEO, AUDIO};
        static _GstElement * acquire(const std::string &location, MEDIA_TYPE mediaType);
        static void release(const std::string &location, MEDIA_TYPE mediaType);
        

    private:
        FileSource();
        ~FileSource();
        bool isLinked();
        void init(const std::string &location);
        void removeVideo();
        void removeAudio();
        
        static bool instanceExists(const std::string &location);
        static void cb_new_src_pad(_GstElement * srcElement, _GstPad * srcPad, int last,
                                   void *data);

        static std::map<std::string, FileSource*> fileSources_;
        _GstElement *filesrc_;
        _GstElement *decodebin_;
        _GstElement *videoQueue_;
        _GstElement *audioQueue_;

        FileSource(const FileSource&); // No copy constructor
        FileSource& operator=(const FileSource&);   // no assignment operator
};

#endif // _FILE_SOURCE_H_