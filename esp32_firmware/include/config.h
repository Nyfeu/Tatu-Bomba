#pragma once

// --- DIRETIVA DE DEBUG ---
#define DEBUG 1

// --- CHAVE DE CONFIGURAÇÃO PARA DEBUG ---
// Defina como 1 para usar a porta USB Serial para debug com o PC.
// Defina como 0 para usar a UART (Serial2) para comunicação com a Raspberry Pi.
#define USE_USB_SERIAL 0

// --- COMUNICAÇÃO COM RASPBERRY PI VIA UART ---
#define RPI_RX_PIN 16
#define RPI_TX_PIN 17

// --- MAPEAMENTO DE PINOS (PINOUT) ---
// Motores
const int enA = 13, in1 = 12, in2 = 14;          // Motor A 
const int enB = 25, in3 = 27, in4 = 26;          // Motor B

// Encoders
const int encoderA_pin = 34;                     // Encoder do Motor A
const int encoderB_pin = 35;                     // Encoder do Motor B

// I2C para MPU6050
const int sda_pin = 21;                          // SDA
const int scl_pin = 22;                          // SCL

// Leitura de Bateria (ADC)
const int batteryPin = 32;                       // Pino ADC para leitura da bateria

// --- CONFIGURAÇÕES DO PWM ---
const int freq = 5000;                           // Frequência do PWM em Hz
const int pwmChannelA = 0, pwmChannelB = 1;      // Canais PWM para os motores A e B
const int resolution = 8;                        // Resolução do PWM em bits (8 bits = 0-255)
const int MAX_PWM_DUTY_CYCLE = 121;              // Máximo ciclo de trabalho para os motores (ajustado para 121)
const int DECCEL_DELAY = 20;                     // Delay em ms para a rampa de desaceleração

// --- CONSTANTES DO FILTRO COMPLEMENTAR ---
const float ALPHA = 0.98;                        // Fator do filtro complementar

// --- CONSTANTES DO DIVISOR DE TENSÃO ---
// R1=10k, R2=2.2k -> Fator = (10000+2200)/2200 = 5.545
const float VOLTAGE_DIVIDER_FACTOR = 5.545;