/**
 * @file main.cpp
 * @brief Controle do robô com ESP32, Encoders, MPU6050 e FreeRTOS.
 *
 * Arquitetura:
 * 1. communication_task: Gerencia Bluetooth (comandos e telemetria).
 * 2. sensor_motor_task: Lê todos os sensores, filtra dados e controla motores.
 * - Mutex (commandMutex): Protege o acesso às variáveis de comando.
 * - Fila (telemetryQueue): Envia dados consolidados dos sensores para a task de comunicação.
 * 
 */

#include <Arduino.h>
#include "BluetoothSerial.h"
#include "driver/pcnt.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

// --- Diretiva de DEBUG ---

#define DEBUG 0

#if DEBUG
  #define DEBUG_PRINT(x)   Serial.print(x)
  #define DEBUG_PRINTLN(x) Serial.println(x)
  #define DEBUG_PRINTF(...) Serial.printf(__VA_ARGS__)
#else
  #define DEBUG_PRINT(x)
  #define DEBUG_PRINTLN(x)
  #define DEBUG_PRINTF(...)
#endif

// --- Objetos e Handles Globais ---
BluetoothSerial SerialBT;
Adafruit_MPU6050 mpu;
TaskHandle_t communicationTaskHandle = NULL;
TaskHandle_t sensorMotorTaskHandle = NULL;
QueueHandle_t telemetryQueue = NULL;
SemaphoreHandle_t commandMutex = NULL;

// --- Estrutura para dados de Telemetria ---
struct TelemetryData {
  int16_t motorA_counts;
  int16_t motorB_counts;
  float accX, accY, accZ;
  float gyroX, gyroY, gyroZ;
};

// --- Mapeamento de Pinos (PINOUT) ---

// Motores
const int enA = 13, in1 = 12, in2 = 14; 
const int enB = 25, in3 = 27, in4 = 26; 

// Encoders
const int encoderA_pin = 34;
const int encoderB_pin = 35;

// I2C para MPU6050
const int sda_pin = 21;
const int scl_pin = 22;

// --- Configurações do PWM ---
const int freq = 5000;
const int pwmChannelA = 0, pwmChannelB = 1;
const int resolution = 8;

// --- Variáveis Globais de Estado (protegidas por Mutex) ---
volatile int motorSpeed = 127; 
volatile char robotState = 'S';

// --- Protótipos das Funções ---
void moveForward();
void moveBackward();
void turnRight();
void turnLeft();
void stopMotors();
void pcnt_init(pcnt_unit_t unit, int pulse_gpio_num);
void communication_task(void *pvParameters);
void sensor_motor_task(void *pvParameters);

void setup() {

  // Tempo para estabilização da bateria
  delay(1000);

  // Caso DEBUG esteja habilitado, inicializa a comunicação serial
  #if DEBUG
    Serial.begin(115200);
  #endif

  // Inicializando a comunicação bluetooth
  SerialBT.begin("Robo_ESP32_Full");

  // Inicializa I2C
  DEBUG_PRINTLN("\nInicializando sistema com Encoders e MPU6050...");
  Wire.begin(sda_pin, scl_pin, 100000); 
  
  // Inicializa MPU6050
  if (!mpu.begin()) {
    DEBUG_PRINTLN("Falha ao encontrar o MPU6050. Verifique as conexões.");
    while (1) vTaskDelay(10);
  }
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  DEBUG_PRINTLN("MPU6050 inicializado.");

  // Inicializa os contadores de pulso
  pcnt_init(PCNT_UNIT_0, encoderA_pin);
  pcnt_init(PCNT_UNIT_1, encoderB_pin);
  DEBUG_PRINTLN("PCNT para encoders inicializado.");

  // Configura pinos dos motores
  pinMode(in1, OUTPUT); pinMode(in2, OUTPUT);
  pinMode(in3, OUTPUT); pinMode(in4, OUTPUT);
  ledcSetup(pwmChannelA, freq, resolution);
  ledcSetup(pwmChannelB, freq, resolution);
  ledcAttachPin(enA, pwmChannelA);
  ledcAttachPin(enB, pwmChannelB);
  stopMotors();

  // --- Criação dos elementos FreeRTOS --- 

  // Fila para dados de Telemetria
  telemetryQueue = xQueueCreate(10, sizeof(TelemetryData)); 

  // Mutex para leitura dos comandos
  commandMutex = xSemaphoreCreateMutex();                   

  // --- Criação das Tarefas ---

  // Tarefa para o gerenciamento da comunicação serial
  xTaskCreate(communication_task, "CommTask", 4096, NULL, 1, &communicationTaskHandle);

  // Tarefa para o gerenciamento dos sensores e acionamento dos motores
  xTaskCreate(sensor_motor_task, "SensorMotorTask", 4096, NULL, 2, &sensorMotorTaskHandle);
  
  // Indica a finalização do setup
  DEBUG_PRINTLN("Setup concluído. Tarefas criadas.");

}

void communication_task(void *pvParameters) {
  TelemetryData receivedData;
  for (;;) {
    if (SerialBT.available()) {
      String commandStr = SerialBT.readStringUntil('\n');
      commandStr.trim();
      if (commandStr.length() > 0) {
        char firstChar = commandStr.charAt(0);
        
        if (xSemaphoreTake(commandMutex, portMAX_DELAY) == pdTRUE) {
          if (toupper(firstChar) == 'V') {
            int percentage = commandStr.substring(1).toInt();
            motorSpeed = map(constrain(percentage, 0, 100), 0, 100, 0, 255);
          } else {
            robotState = toupper(firstChar);
          }
          xSemaphoreGive(commandMutex);
        }
      }
    }

    if (xQueueReceive(telemetryQueue, &receivedData, 0) == pdPASS) {
      char buffer[200];
      int16_t signed_A = receivedData.motorA_counts;
      int16_t signed_B = receivedData.motorB_counts;
      
      if (robotState == 'B') { signed_A = -signed_A; signed_B = -signed_B; } 
      else if (robotState == 'L') { signed_A = -signed_A; } 
      else if (robotState == 'R') { signed_B = -signed_B; }

      sprintf(buffer, "E(A:%d,B:%d) A(X:%.2f,Y:%.2f) G(X:%.2f,Y:%.2f)\n", 
              signed_A, signed_B,
              receivedData.accX, receivedData.accY,
              receivedData.gyroX, receivedData.gyroY);
      SerialBT.print(buffer);
    }
    vTaskDelay(pdMS_TO_TICKS(50));
  }
}

void sensor_motor_task(void *pvParameters) {
  char localRobotState;
  TelemetryData dataToSend;
  sensors_event_t a, g, temp;

  const int MOVING_AVG_SIZE = 5;
  int16_t readings_A[MOVING_AVG_SIZE] = {0}; long total_A = 0; int index_A = 0;
  int16_t readings_B[MOVING_AVG_SIZE] = {0}; long total_B = 0; int index_B = 0;

  for (;;) {
    // 1. Ler contadores brutos dos encoders
    int16_t raw_counts_A, raw_counts_B;
    pcnt_get_counter_value(PCNT_UNIT_0, &raw_counts_A);
    pcnt_get_counter_value(PCNT_UNIT_1, &raw_counts_B);
    pcnt_counter_clear(PCNT_UNIT_0);
    pcnt_counter_clear(PCNT_UNIT_1);

    // 2. Aplicar Média Móvel nos encoders
    total_A = total_A - readings_A[index_A];
    readings_A[index_A] = raw_counts_A;
    total_A = total_A + readings_A[index_A];
    index_A = (index_A + 1) % MOVING_AVG_SIZE;
    dataToSend.motorA_counts = total_A / MOVING_AVG_SIZE;

    total_B = total_B - readings_B[index_B];
    readings_B[index_B] = raw_counts_B;
    total_B = total_B + readings_B[index_B];
    index_B = (index_B + 1) % MOVING_AVG_SIZE;
    dataToSend.motorB_counts = total_B / MOVING_AVG_SIZE;
    
    // 3. Ler MPU6050
    mpu.getEvent(&a, &g, &temp);
    dataToSend.accX = a.acceleration.x;
    dataToSend.accY = a.acceleration.y;
    dataToSend.accZ = a.acceleration.z;
    dataToSend.gyroX = g.gyro.x;
    dataToSend.gyroY = g.gyro.y;
    dataToSend.gyroZ = g.gyro.z;

    // 4. Enviar todos os dados para a fila de telemetria
    xQueueSend(telemetryQueue, &dataToSend, 0);

    // 5. Ler estado do robô de forma segura
    if (xSemaphoreTake(commandMutex, portMAX_DELAY) == pdTRUE) {
      localRobotState = robotState;
      xSemaphoreGive(commandMutex);
    }

    // 6. Atuar nos motores
    switch (localRobotState) {
      case 'F': moveForward(); break;
      case 'B': moveBackward(); break;
      case 'L': turnLeft(); break;
      case 'R': turnRight(); break;
      case 'S': stopMotors(); break;
      default: stopMotors(); break;
    }
    vTaskDelay(pdMS_TO_TICKS(20));
  }
}

void pcnt_init(pcnt_unit_t unit, int pulse_gpio_num) {
    pcnt_config_t pcnt_config = { .pulse_gpio_num = pulse_gpio_num, .ctrl_gpio_num = PCNT_PIN_NOT_USED, .lctrl_mode = PCNT_MODE_REVERSE, .hctrl_mode = PCNT_MODE_KEEP, .pos_mode = PCNT_COUNT_INC, .neg_mode = PCNT_COUNT_DIS, .counter_h_lim = 32767, .counter_l_lim = -32768, .unit = unit, .channel = PCNT_CHANNEL_0, };
    pcnt_unit_config(&pcnt_config);
    pcnt_counter_pause(unit); pcnt_counter_clear(unit); pcnt_counter_resume(unit);
}

void loop() {}

void moveForward() {
  digitalWrite(in1, HIGH); digitalWrite(in2, LOW);
  digitalWrite(in3, HIGH); digitalWrite(in4, LOW);
  ledcWrite(pwmChannelA, motorSpeed); ledcWrite(pwmChannelB, motorSpeed);
}
void moveBackward() {
  digitalWrite(in1, LOW); digitalWrite(in2, HIGH);
  digitalWrite(in3, LOW); digitalWrite(in4, HIGH);
  ledcWrite(pwmChannelA, motorSpeed); ledcWrite(pwmChannelB, motorSpeed);
}
void turnRight() {
  digitalWrite(in1, HIGH); digitalWrite(in2, LOW);
  digitalWrite(in3, LOW); digitalWrite(in4, HIGH);
  ledcWrite(pwmChannelA, motorSpeed); ledcWrite(pwmChannelB, motorSpeed);
}
void turnLeft() {
  digitalWrite(in1, LOW); digitalWrite(in2, HIGH);
  digitalWrite(in3, HIGH); digitalWrite(in4, LOW);
  ledcWrite(pwmChannelA, motorSpeed); ledcWrite(pwmChannelB, motorSpeed);
}
void stopMotors() {
  digitalWrite(in1, LOW); digitalWrite(in2, LOW);
  digitalWrite(in3, LOW); digitalWrite(in4, LOW);
  ledcWrite(pwmChannelA, 0); ledcWrite(pwmChannelB, 0);
}

