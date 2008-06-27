#include "oscThread.h"
#include <iostream>

#include <list>
#include <vector>

int main(int argc,char** argv)
{
   OscThread t;
 
   QueuePairOfOscMessage q = t.getInvertQueue();

   t.run();

   while(1)
   {
        OscMessage m = q.copy_timed_pop(100);

        if(!m.path.empty())
            std::cout << m.path << std::endl;
        q.done(&m);
    }

}

