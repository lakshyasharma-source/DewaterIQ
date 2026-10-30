#include "diq_app.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>

void diq_app_init(DiqApp *app, Scenario scenario, uint32_t seed) {
    if (!app) return;
    memset(app, 0, sizeof(*app));
    app->seed = seed;
    app->scenario = scenario;
    sim_init(&app->simulator, scenario, seed);
    /* The host prefixes a capture ID before inserting into the historian. */
    (void)snprintf(app->run_id, sizeof(app->run_id),
                   "stm32-synthetic-%s-seed%lu", scenario_name(scenario),
                   (unsigned long)seed);
}

int diq_app_step(DiqApp *app, char *output, size_t capacity) {
    if (!app || !output || capacity < 2u) return -1;
    Record record;
    sim_step(&app->simulator, &record);
    record.centrifuge_id = "CENT-STM32-SIM-01";
    record.event = detect_event(&app->detector, &record);
    return diq_format_json(output, capacity, &record, app->run_id);
}

static void put_reply(char *out, size_t capacity, const char *msg) {
    if (out && capacity) (void)snprintf(out, capacity, "%s", msg);
}

int diq_app_command(DiqApp *app, const char *command, char *reply, size_t capacity) {
    if (!app || !command || !reply || capacity == 0u) return -1;
    if (strcmp(command, "HELP") == 0) {
        put_reply(reply, capacity, "Commands: HELP | LIST | SCENARIO <name> | RESET | SEED <uint>");
        return 0;
    }
    if (strcmp(command, "LIST") == 0) {
        size_t pos = 0;
        for (int i = 0; i < (int)S_COUNT; ++i) {
            const char *name = scenario_name((Scenario)i);
            int n = snprintf(reply + pos, capacity - pos, "%s%s", i ? "," : "", name);
            if (n < 0 || (size_t)n >= capacity - pos) { reply[0] = '\0'; return -1; }
            pos += (size_t)n;
        }
        return 0;
    }
    if (strcmp(command, "RESET") == 0) {
        diq_app_init(app, app->scenario, app->seed);
        put_reply(reply, capacity, "Reset synthetic state and detector");
        return 0;
    }
    if (strncmp(command, "SCENARIO ", 9) == 0) {
        Scenario scenario;
        const char *name = command + 9;
        if (scenario_parse(name, &scenario)) {
            diq_app_init(app, scenario, app->seed);
            (void)snprintf(reply, capacity, "Scenario switched: %s", name);
            return 0;
        }
        put_reply(reply, capacity, "Unknown scenario. Send LIST");
        return -1;
    }
    if (strncmp(command, "SEED ", 5) == 0) {
        const char *num = command + 5;
        if (!*num || *num == '-') { put_reply(reply,capacity,"Invalid seed"); return -1; }
        errno = 0;
        char *end = NULL;
        unsigned long value = strtoul(num, &end, 10);
        if (errno || end == num || *end != '\0' || value > UINT32_MAX) {
            put_reply(reply, capacity, "Invalid seed"); return -1;
        }
        diq_app_init(app, app->scenario, (uint32_t)value);
        put_reply(reply, capacity, "Synthetic replay seed changed");
        return 0;
    }
    put_reply(reply, capacity, "Unknown command. Send HELP");
    return -1;
}
