CC ?= cc
CFLAGS ?= -std=c99 -O2 -Wall -Wextra -Wpedantic -Werror
CPPFLAGS = -Iinclude
SOURCES = src/main.c src/simulator.c src/detector.c src/telemetry.c
OBJECTS = $(SOURCES:.c=.o)
TARGET = dewateriq_sim
.PHONY: all clean test
all: $(TARGET)
$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $(OBJECTS) -lm
src/%.o: src/%.c include/dewateriq.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@
test: $(TARGET)
	./$(TARGET) --scenario stable --samples 20 --seed 7 > /tmp/dewateriq-test-a.ndjson
	./$(TARGET) --scenario stable --samples 20 --seed 7 > /tmp/dewateriq-test-b.ndjson
	cmp /tmp/dewateriq-test-a.ndjson /tmp/dewateriq-test-b.ndjson
	@echo 'C deterministic replay PASSED'
clean:
	rm -f $(OBJECTS) $(TARGET)
