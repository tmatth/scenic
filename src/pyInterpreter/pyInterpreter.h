#include <string>


class pyInterpreter
{
public:

    int init(int argc,char* argv[]);

    std::string run_str(std::string s);    
    std::string run_input();
    void interact();




};

