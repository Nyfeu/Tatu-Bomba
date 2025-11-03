#include "globals.h"

// --- DEFINIÇÃO DAS VARIÁVEIS E OBJETOS GLOBAIS ---

Adafruit_MPU6050 mpu;
TaskHandle_t communicationTaskHandle = NULL;
TaskHandle_t sensorMotorTaskHandle = NULL;
QueueHandle_t telemetryQueue = NULL;
SemaphoreHandle_t commandMutex = NULL;

volatile int motorSpeed = 127;
volatile char robotState = 'S';

float anglePitch = 0.0;
float angleRoll = 0.0;
unsigned long last_filter_time = 0;

// Condicionalmente define o objeto SerialRPi apenas se não estiver no modo USB
#if !USE_USB_SERIAL
    HardwareSerial SerialRPi(2);
#endif