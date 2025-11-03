#pragma once

#include <Arduino.h>
#include "config.h" 
#include "HardwareSerial.h"
#include "driver/pcnt.h"
#include "esp_adc_cal.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

// --- ESTRUTURA PARA DADOS DE TELEMETRIA ---
struct __attribute__((packed)) TelemetryData {
  int64_t  timestamp_us;
  float    pitch;
  float    roll;
  int16_t  gyro_z_raw;
  int32_t  left_encoder;   
  int32_t  right_encoder;  
  uint16_t battery_mv;
  uint8_t  checksum;
};

// --- OBJETOS E HANDLES GLOBAIS (EXTERN) ---
extern Adafruit_MPU6050 mpu;
extern TaskHandle_t communicationTaskHandle;
extern TaskHandle_t sensorMotorTaskHandle;
extern QueueHandle_t telemetryQueue;
extern SemaphoreHandle_t commandMutex;

// Declara o SerialRPi apenas se estiver no modo de produção (não USB)
#if !USE_USB_SERIAL
  extern HardwareSerial SerialRPi;
#endif

// --- VARIÁVEIS GLOBAIS DE ESTADO (EXTERN) ---
extern volatile int motorSpeed;
extern volatile char robotState;

// --- VARIÁVEIS DO FILTRO (EXTERN) ---
extern float anglePitch;
extern float angleRoll;
extern unsigned long last_filter_time;

// --- MACROS DE DEBUG ---

#if USE_USB_SERIAL
  #define CommsSerial Serial
#else
  #define CommsSerial SerialRPi
#endif

#if DEBUG
  #define DEBUG_PRINT(x)   Serial.print(x)
  #define DEBUG_PRINTLN(x) Serial.println(x)
  #define DEBUG_PRINTF(...) Serial.printf(__VA_ARGS__)
#else
  #define DEBUG_PRINT(x)
  #define DEBUG_PRINTLN(x)
  #define DEBUG_PRINTF(...)
#endif