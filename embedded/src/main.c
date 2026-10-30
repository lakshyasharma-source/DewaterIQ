#include "dewateriq.h"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

static void usage(const char *prog) {
    fprintf(stderr,"Usage: %s [--scenario NAME] [--samples 1..100000] [--seed UINT] [--centrifuge-id ID] [--list-scenarios]\n",prog);
}
static int safe_identifier(const char *text) {
    size_t n=strlen(text);
    if (!n || n>24) return 0;
    for (size_t i=0;i<n;i++) {
        if (!isalnum((unsigned char)text[i]) && text[i]!='_' && text[i]!='-') return 0;
    }
    return 1;
}
static int parse_ulong(const char *txt, unsigned long max, unsigned long *out) {
    char *end=NULL; errno=0;
    unsigned long v=strtoul(txt,&end,10);
    if (errno || end==txt || *end!='\0' || txt[0]=='-' || v>max) return 0;
    *out=v; return 1;
}
int main(int argc,char **argv) {
    Scenario scenario=S_STABLE; unsigned long samples=60, seed=7;
    const char *centrifuge="CENT-SIM-01";
    for (int i=1;i<argc;i++) {
        if (!strcmp(argv[i],"--list-scenarios")) {
            for (int j=0;j<S_COUNT;j++) { puts(scenario_name((Scenario)j)); }
            return 0;
        } else if (!strcmp(argv[i],"--scenario") && i+1<argc) {
            if (!scenario_parse(argv[++i],&scenario)) { usage(argv[0]); return 2; }
        } else if (!strcmp(argv[i],"--centrifuge-id") && i+1<argc) {
            centrifuge=argv[++i];
            if (!safe_identifier(centrifuge)) { fprintf(stderr,"Invalid simulation ID\n"); return 2; }
        } else if (!strcmp(argv[i],"--samples") && i+1<argc) {
            if (!parse_ulong(argv[++i],100000,&samples) || !samples) return 2;
        } else if (!strcmp(argv[i],"--seed") && i+1<argc) {
            if (!parse_ulong(argv[++i],4294967295UL,&seed)) return 2;
        } else { usage(argv[0]); return 2; }
    }
    char run_id[80]; snprintf(run_id,sizeof(run_id),"synthetic-%s-seed%lu-%s",scenario_name(scenario),seed,centrifuge);
    Simulator s; sim_init(&s,scenario,(uint32_t)seed); Detector detector={0};
    for (unsigned long i=0;i<samples;i++) {
        Record cur; sim_step(&s,&cur);
        cur.centrifuge_id=centrifuge;
        cur.event=detect_event(&detector,&cur);
        print_json(stdout,&cur,run_id);
    }
    return ferror(stdout)?1:0;
}
