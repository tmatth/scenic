#include "gstThread.h"
#include "osc/osc.h"
#include "gutil/optionArgs.h"


int m (int argc, char** argv)
{
    GstThread gst;
    OscThread o;
    OptionArgs opts;

    opts.add(gst.get_args());
    opts.add(o.get_args());

    if(!opts.parse(argc, argv))
        return 1;
    QueuePair &gst_queue = gst.getQueue();
    OscQueue &osc_queue = o.getQueue();
    if(!gst.run())
        return -1;
    if(!o.run())
        return -1;
    while(1)
    {
        OscMessage m = osc_queue.timed_pop(10000);

        if(m.path.empty())
            continue;
        if(!m.path.compare("/quit"))
        {
            BaseMessage in(BaseMessage::QUIT);
            gst_queue.push(in);
            osc_queue.push(OscMessage("/quit", "", 0, 0, 0));
            break;
        }
        if(m.path.compare("/gst"))
            continue;
        LOG(m.args[0].s);
        if(!m.args[0].s.compare("init")){
            BaseMessage in(BaseMessage::INIT);
            gst_queue.push(in);
        }
        if(!m.args[0].s.compare("start")){
            BaseMessage start(BaseMessage::START);
            gst_queue.push(start);
        }
        if(!m.args[0].s.compare("stop")){
            BaseMessage stop(BaseMessage::STOP);
            gst_queue.push(stop);
        }
    }

    std::cout << "Done!" << std::endl;
    return 0;
}


int main (int argc, char** argv)
{
    return m(argc, argv);
}


//./mainTester -s videotestsrc --oscLocal=7770 --oscRemote=7771 --oscRemoteHost=127.0.0.1
