#include "diq_stm32_board.h"
#include <stdio.h>
#include <string.h>
UART_HandleTypeDef huart1 = {1};
static uint32_t fake_time=0;
static unsigned int json_seen=0;
uint32_t HAL_GetTick(void) { return fake_time; }
HAL_StatusTypeDef HAL_UART_Transmit(UART_HandleTypeDef *h, uint8_t *b, uint16_t n, uint32_t timeout) {
    (void)h; (void)timeout;
    if (n > 0 && b[0] == '{' && memchr(b, '\n', n) != NULL) json_seen++;
    return HAL_OK;
}
HAL_StatusTypeDef HAL_UART_Receive_IT(UART_HandleTypeDef *h, uint8_t *b, uint16_t n) {
    (void)h; (void)b; (void)n; return HAL_OK;
}
int main(void) {
    DIQ_STM32_Init();
    for (int i=0; i<3; i++) { fake_time+=1000; DIQ_STM32_Poll(); }
    if (json_seen!=3) {fprintf(stderr,"unexpected frames: %u\n",json_seen); return 1;}
    puts("Stub HAL board integration OK (not physical device)");
    return 0;
}
