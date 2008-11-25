
/** glVideoSink.cpp
 * Copyright 2008 Koya Charles & Tristan Matthews 
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

#include <cassert>

#include <gst/interfaces/xoverlay.h>

#include "gstLinkable.h"
#include "logWriter.h"
#include "pipeline.h"

#include <gtk/gtk.h>
#include <gdk/gdk.h>
#include <gdk/gdkkeysyms.h>
#include <gdk/gdkx.h>
#include <X11/extensions/Xinerama.h>

#include <GL/glu.h>

#include "glVideoSink.h"
        
const GLfloat GLImageSink::INIT_X = -0.67f;     
const GLfloat GLImageSink::INIT_Y = -0.5f;
const GLfloat GLImageSink::INIT_Z = -1.2;
#if 0
const GLfloat GLImageSink::INIT_X = -1.25625f;     
const GLfloat GLImageSink::INIT_Y = -0.93750f;
const GLfloat GLImageSink::INIT_Z = -1.2f;
#endif

const GLfloat GLImageSink::INIT_LEFT_CROP = 0.0;
const GLfloat GLImageSink::INIT_RIGHT_CROP = 0.0;
const GLfloat GLImageSink::INIT_BOTTOM_CROP = 0.0;
const GLfloat GLImageSink::INIT_TOP_CROP = 0.0;
const GLfloat GLImageSink::STEP = 0.01;

GLfloat GLImageSink::x_ = INIT_X;
GLfloat GLImageSink::y_ = INIT_Y;
GLfloat GLImageSink::z_ = INIT_Z;
GLfloat GLImageSink::leftCrop_ = INIT_LEFT_CROP;
GLfloat GLImageSink::rightCrop_ = INIT_RIGHT_CROP;
GLfloat GLImageSink::topCrop_ = INIT_TOP_CROP;
GLfloat GLImageSink::bottomCrop_ = INIT_BOTTOM_CROP;

gboolean GLImageSink::reshapeCallback(GLuint width, GLuint height)
{
    //z_ = width == 640 ? -1.4240 : INIT_Z;
    g_print("WIDTH: %u, HEIGHT: %u", width, height);
    glViewport(0, 0, width, height);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    gluPerspective(45, (gfloat) width / (gfloat) height, 0.1, 100);  
    glMatrixMode(GL_MODELVIEW);	
    return TRUE;
}


gboolean GLImageSink::drawCallback(GLuint texture, GLuint width, GLuint height)
{
    static GTimeVal current_time;
    static glong last_sec = current_time.tv_sec;
    static glong last_usec = current_time.tv_usec;
    static gint nbFrames = 0;  

    g_get_current_time (&current_time);
    if((current_time.tv_sec - last_sec < 1) && (current_time.tv_usec - last_usec < 5000))
    {	
        usleep((current_time.tv_usec - last_usec) >> 1);
        return FALSE;
    }
    nbFrames++ ;
    last_usec = current_time.tv_usec ;	
    if ((current_time.tv_sec - last_sec) >= 1)
    {
        LOG_DEBUG("GRAPHIC FPS = " << nbFrames << std::endl);

        nbFrames = 0;
        last_sec = current_time.tv_sec;
    }

    glEnable(GL_DEPTH_TEST);
    glMatrixMode(GL_MODELVIEW);
    gfloat aspectRatio = (gfloat) width / (gfloat) height;
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    glLoadIdentity();
    glColor3f(0.0f,0.0f,0.0f);
    glTranslatef(x_, y_, z_);
    glTranslatef(rightCrop_, bottomCrop_,  0.01f);

    glBegin(GL_TRIANGLE_FAN);
    glVertex3f(aspectRatio,0.0f,0.0f);
    glVertex3f(0.0f, 0.0f, 0.0f);
    glVertex3f(0.0f,  -1.0f, 0.0f);
    glVertex3f(2*aspectRatio,  -1.0f, 0.0f); 
    glVertex3f(2*aspectRatio,  1.0f, 0.0f);
    glVertex3f(aspectRatio,  1.0f, 0.0f);
    glEnd();

    glEnable (GL_TEXTURE_RECTANGLE_ARB);
    glBindTexture (GL_TEXTURE_RECTANGLE_ARB, texture);
    glTexParameteri (GL_TEXTURE_RECTANGLE_ARB, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri (GL_TEXTURE_RECTANGLE_ARB, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri (GL_TEXTURE_RECTANGLE_ARB, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri (GL_TEXTURE_RECTANGLE_ARB, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexEnvi (GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE);

    glLoadIdentity();

    glTranslatef(x_, y_, z_);

    glBegin(GL_QUADS);
    glTexCoord2f(0.0f, 0.0f);  glVertex3f(0.0f, 1.0f, 0.0f);
    glTexCoord2f((gfloat)width-1, 0.0f);  glVertex3f(aspectRatio,  1.0f, 0.0f);
    glTexCoord2f((gfloat) width-1, (gfloat) height); glVertex3f(aspectRatio,  0.0f, 0.0f);
    glTexCoord2f(0.0f, height); glVertex3f(0.0f, 0.0f, 0.0f);
    glEnd();

    //return TRUE causes a postRedisplay
    return FALSE;
}


gboolean GLImageSink::key_press_event_cb(GtkWidget *widget, GdkEventKey *event, gpointer /*data*/)
{
    switch (event->keyval) {
        case 'f':
            toggleFullscreen(widget);
            break;
        case 'x':
        case GDK_Right:
            x_ += STEP;
            break;
        case 'X':
        case GDK_Left:
            x_ -= STEP;
            break;
        case 'y':
        case GDK_Down:
            y_ += STEP;
            break;
        case 'Y':
        case GDK_Up:
            y_ -= STEP;
            break;
        case 'z':
            z_ += STEP;
            break;
        case 'Z':
            z_ -= STEP;
            break;
        case 'b':
            bottomCrop_ += STEP;
            break;
        case 'B':
            bottomCrop_ -= STEP;
            break;
        case 't':
            topCrop_ -= STEP;
            break;
        case 'T':
            topCrop_ += STEP;
            break;
        case 'r':
            rightCrop_ -= STEP;
            break;
        case 'R':
            rightCrop_ += STEP;
            break;
        case 'l':
            leftCrop_ += STEP;
            break;
        case 'L':
            leftCrop_ -= STEP;
            break;
        default:
            g_print("unknown keypress %d", event->keyval);
            break;
    }
    LOG_INFO("x:" << x_  <<
            " y:" << y_ <<
            " z:" << z_ <<
            " l:" << leftCrop_ <<
            " r:" << rightCrop_ <<
            " t:" <<  topCrop_ <<
            " b:" << bottomCrop_);


    return TRUE;
}


gboolean GLImageSink::mouse_wheel_cb(GtkWidget * /*widget*/, GdkEventScroll *event, gpointer /*data*/)
{
    switch (event->direction)
    {
        case GDK_SCROLL_UP:
            z_ += STEP;
            break;
        case GDK_SCROLL_DOWN:
            z_ -= STEP;
            break;
        default:
            g_print("Unhandled mouse wheel event");
            break;
    }
    return TRUE;
}


void GLImageSink::resetGLparams()
{
    // reset persistent static params to their initial values

    x_ = INIT_X;
    y_ = INIT_Y;
    z_ = INIT_Z; 
    leftCrop_ = INIT_LEFT_CROP;
    rightCrop_ = INIT_RIGHT_CROP;
    bottomCrop_ = INIT_BOTTOM_CROP;
    topCrop_ = INIT_TOP_CROP;
}


GLImageSink::~GLImageSink()
{
    resetGLparams();

    Pipeline::Instance()->remove(&glUpload_);
    VideoSink::destroySink();
    if (window_)
    {
        gtk_widget_destroy(window_);
        LOG_DEBUG("Widget destroyed");
    }
}

void GLImageSink::init()
{
    static bool gtk_initialized = false;
    if (!gtk_initialized)
        gtk_init(0, NULL);

    glUpload_ = Pipeline::Instance()->makeElement("glupload", "colorspace");

    sink_ = Pipeline::Instance()->makeElement("glimagesink", "videosink");
    g_object_set(G_OBJECT(sink_), "sync", FALSE, NULL);

    gstlinkable::link(glUpload_, sink_);

    window_ = gtk_window_new(GTK_WINDOW_TOPLEVEL);    
    assert(window_);


    GdkDisplay* display = gdk_display_get_default();
    assert(display);
    int n;
    XineramaScreenInfo* xine = XineramaQueryScreens(GDK_DISPLAY_XDISPLAY(display),&n);
    if(!xine)
        n = 0; // don't query ScreenInfo
    for(int j=0;j<n;j++)
    {
        LOG_INFO(   "req:" << screen_num_ << 
                " screen:" << xine[j].screen_number << 
                " x:" << xine[j].x_org << 
                " y:" << xine[j].y_org << 
                " width:" << xine[j].width << 
                " height:" << xine[j].height);
        if (j == screen_num_) 
            gtk_window_move(GTK_WINDOW(window_),xine[j].x_org,xine[j].y_org);
    }

    gtk_window_set_default_size(GTK_WINDOW(window_), WIDTH, HEIGHT);
    gtk_window_set_decorated(GTK_WINDOW(window_), FALSE);   // gets rid of border/title
    g_signal_connect(G_OBJECT(window_), "expose-event", G_CALLBACK(
                expose_cb), static_cast<void*>(this));
    g_signal_connect(G_OBJECT(window_), "key-press-event",
            G_CALLBACK(key_press_event_cb), NULL);
    g_signal_connect(G_OBJECT(window_), "scroll-event",
            G_CALLBACK(mouse_wheel_cb), NULL);
    gtk_widget_set_events(window_, GDK_KEY_PRESS_MASK);
    gtk_widget_set_events(window_, GDK_SCROLL_MASK);

    /* configure elements */
    g_object_set(G_OBJECT(sink_), "client-reshape-callback", G_CALLBACK(reshapeCallback), NULL);
    g_object_set(G_OBJECT(sink_), "client-draw-callback", G_CALLBACK(drawCallback), NULL);  
    showWindow();
}

