CC ?= gcc
CFLAGS ?= -std=c99 -Wall -Wextra -Wpedantic -Werror -O2
INCLUDES = -I../Inc -I../../embedded/include
SOURCES = host_smoke.c ../Src/diq_app.c ../../embedded/src/simulator.c ../../embedded/src/detector.c ../../embedded/src/telemetry.c
.PHONY: all test clean
all: host_smoke
host_smoke: $(SOURCES)
	$(CC) $(CFLAGS) $(INCLUDES) $(SOURCES) -lm -o $@
test: host_smoke
	./host_smoke load > /tmp/dewateriq-u575-frames.ndjson
	@echo 'Portable STM32 edge-layer host smoke PASSED'
clean:
	rm -f host_smoke board-stub

board-stub: ../tests/test_board_stub.c ../Src/diq_stm32_board.c ../Src/diq_app.c ../../embedded/src/simulator.c ../../embedded/src/detector.c ../../embedded/src/telemetry.c
	$(CC) $(CFLAGS) -I../tests/stubs $(INCLUDES) $^ -lm -o $@
