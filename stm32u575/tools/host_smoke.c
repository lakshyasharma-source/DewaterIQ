#include "diq_app.h"
#include <stdio.h>
#include <string.h>
#include <stdint.h>
int main(int argc, char **argv) {
    Scenario scenario = S_STABLE;
    if (argc>1 && !scenario_parse(argv[1],&scenario)) return 2;
    DiqApp app;
    diq_app_init(&app,scenario,7u);
    for (int i=0; i<65; ++i) {
        char buffer[DIQ_STM32_JSON_CAPACITY];
        int n=diq_app_step(&app,buffer,sizeof(buffer));
        if (n<=0) return 3;
        fwrite(buffer,1,(size_t)n,stdout);
    }
    char response[256];
    if (diq_app_command(&app,"SCENARIO barite-recovery",response,sizeof(response))) return 4;
    if (app.scenario != S_BARITE || app.simulator.tick != 0) return 5;
    if (diq_app_command(&app,"LIST",response,sizeof(response))) return 6;
    if (!strstr(response,"barite-recovery")) return 7;
    if (diq_app_command(&app,"SEED 4294967296",response,sizeof(response)) == 0) return 8;
    return 0;
}
