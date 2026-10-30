#include "diq_stm32_board.h"
#include "diq_app.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* CubeMX must provide huart1 for USART1 115200-8N1, global IRQ enabled. */
extern UART_HandleTypeDef huart1;

static DiqApp app;
static char tx_frame[DIQ_STM32_JSON_CAPACITY];
static uint8_t rx_byte;
static volatile uint8_t command_ready;
static char input_line[80];
static volatile uint32_t input_length;
static char pending_line[80];
static uint32_t last_sample_ms;

static void send_comment(const char *message) {
    char line[256];
    int len = snprintf(line, sizeof(line), "# %s\r\n", message);
    if (len > 0 && (size_t)len < sizeof(line)) {
        (void)HAL_UART_Transmit(&huart1, (uint8_t *)line, (uint16_t)len, 250u);
    }
}

void DIQ_STM32_Init(void) {
    diq_app_init(&app, S_STABLE, 7u);
    command_ready = 0u;
    input_length = 0u;
    last_sample_ms = HAL_GetTick();
    (void)HAL_UART_Receive_IT(&huart1, &rx_byte, 1u);
    send_comment("DewaterIQ STM32U575 synthetic simulation / READ ONLY / 115200 8N1");
    send_comment("Commands: HELP, LIST, SCENARIO <name>, RESET, SEED <uint>");
}

void DIQ_STM32_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart != &huart1) return;
    if (rx_byte == '\r' || rx_byte == '\n') {
        if (!command_ready && input_length > 0u) {
            input_line[input_length] = '\0';
            memcpy(pending_line, input_line, input_length + 1u);
            command_ready = 1u;
        }
        input_length = 0u;
    } else if (!command_ready) {
        if (input_length < sizeof(input_line) - 1u)
            input_line[input_length++] = (char)rx_byte;
        else input_length = 0u; /* discard oversized line */
    }
    (void)HAL_UART_Receive_IT(&huart1, &rx_byte, 1u);
}

void DIQ_STM32_UartErrorCallback(UART_HandleTypeDef *huart) {
    if (huart == &huart1) (void)HAL_UART_Receive_IT(&huart1, &rx_byte, 1u);
}

void DIQ_STM32_Poll(void) {
    if (command_ready) {
        char command[sizeof(pending_line)];
        /* Protect the single-slot interrupt-to-main command mailbox. */
        uint32_t primask = __get_PRIMASK();
        __disable_irq();
        memcpy(command, pending_line, sizeof(command));
        command_ready = 0u;
        if (!primask) __enable_irq();
        char reply[256];
        (void)diq_app_command(&app, command, reply, sizeof(reply));
        send_comment(reply);
        last_sample_ms = HAL_GetTick();
    }
    uint32_t now = HAL_GetTick();
    if ((uint32_t)(now - last_sample_ms) >= 1000u) {
        last_sample_ms = now;
        int bytes = diq_app_step(&app, tx_frame, sizeof(tx_frame));
        if (bytes > 0 && bytes <= UINT16_MAX) {
            if (HAL_UART_Transmit(&huart1, (uint8_t *)tx_frame,
                                  (uint16_t)bytes, 700u) != HAL_OK) {
                /* Simulator continues; no physical-control path. */
            }
        } else {
            send_comment("ERROR: telemetry frame too large");
        }
    }
}
