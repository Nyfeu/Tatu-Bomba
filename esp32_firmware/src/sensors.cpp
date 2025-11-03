#include "globals.h"
#include "config.h"

void pcnt_init(pcnt_unit_t unit, int pulse_gpio_num) {
    pcnt_config_t pcnt_config = {
        .pulse_gpio_num = pulse_gpio_num,
        .ctrl_gpio_num = PCNT_PIN_NOT_USED,
        .lctrl_mode = PCNT_MODE_REVERSE,
        .hctrl_mode = PCNT_MODE_KEEP,
        .pos_mode = PCNT_COUNT_INC,
        .neg_mode = PCNT_COUNT_DIS,
        .counter_h_lim = 32767,
        .counter_l_lim = -32768,
        .unit = unit,
        .channel = PCNT_CHANNEL_0,
    };
    pcnt_unit_config(&pcnt_config);
    pcnt_counter_pause(unit);
    pcnt_counter_clear(unit);
    pcnt_counter_resume(unit);
}

void setupMPU() {
    if (!mpu.begin()) {
        DEBUG_PRINTLN("Falha ao encontrar o MPU6050. Verifique as conexões.");
        while (1) vTaskDelay(10);
    }
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    DEBUG_PRINTLN("MPU6050 inicializado.");
}

void setupEncoders() {
    pcnt_init(PCNT_UNIT_0, encoderA_pin);
    pcnt_init(PCNT_UNIT_1, encoderB_pin);
    DEBUG_PRINTLN("PCNT para encoders inicializado.");
}

void setupADC() {

    // Configura a atenuação do pino ADC da bateria para permitir a leitura da
    // faixa de tensão completa (0 a 3.3V). 
    analogSetPinAttenuation((gpio_num_t)batteryPin, ADC_11db);
    DEBUG_PRINTLN("ADC para leitura da bateria inicializado.");

}