#include "globals.h"
#include "config.h"
#include "motors.h"

// --- CONSTANTES PARA COMUNICAÇÃO ---

// Start of Packet para comunicação binária
const uint8_t SOP[] = {0xAA, 0x55};


// --- TAREFA DE COMUNICAÇÃO ---
void communication_task(void *pvParameters) {
  TelemetryData receivedData;
  for (;;) {
    // 1. LER COMANDOS DA PORTA DE COMUNICAÇÃO ATIVA
    if (CommsSerial.available()) {
      String commandStr = CommsSerial.readStringUntil('\n');
      
      // ---> LOG 1: Mostra o comando bruto exatamente como foi recebido <---
      DEBUG_PRINTF("[COMM] Comando bruto recebido: '%s'\n", commandStr.c_str());

      commandStr.trim();
      if (xSemaphoreTake(commandMutex, (TickType_t) 10) == pdTRUE) {
        if (commandStr.startsWith("DRIVE:")) {
          String values = commandStr.substring(6);
          int commaIndex = values.indexOf(',');
          if (commaIndex != -1) {
            int leftSpeed = values.substring(0, commaIndex).toInt();
            int rightSpeed = values.substring(commaIndex + 1).toInt();

            // ---> LOG 2: Mostra os valores após o parsing <---
            DEBUG_PRINTF("[COMM] Comando DRIVE parseado: Esq=%d, Dir=%d\n", leftSpeed, rightSpeed);

            int speed = max(abs(leftSpeed), abs(rightSpeed));
            motorSpeed = map(speed, 0, 100, 0, MAX_PWM_DUTY_CYCLE);
            if (leftSpeed > 0 && rightSpeed > 0) robotState = 'F';
            else if (leftSpeed < 0 && rightSpeed < 0) robotState = 'B';
            else if (leftSpeed < 0 && rightSpeed > 0) robotState = 'L';
            else if (leftSpeed > 0 && rightSpeed < 0) robotState = 'R';
            else robotState = 'S';
          }
        } else {
          robotState = 'S';
        }
        xSemaphoreGive(commandMutex);
      }
    }

    // 2. ENVIAR TELEMETRIA PARA A PORTA DE COMUNICAÇÃO ATIVA (Lógica inalterada)
    if (xQueueReceive(telemetryQueue, &receivedData, 0) == pdPASS) {
      #if USE_USB_SERIAL
        CommsSerial.printf("Pitch: %.2f, Roll: %.2f, EncL: %d, EncR: %d, Batt: %dmV\n",
                           receivedData.pitch, receivedData.roll,
                           receivedData.left_encoder, receivedData.right_encoder,
                           receivedData.battery_mv);
      #else
        CommsSerial.write(SOP, sizeof(SOP));
        CommsSerial.write((uint8_t*)&receivedData, sizeof(TelemetryData));
      #endif
    }
    
    vTaskDelay(pdMS_TO_TICKS(20));
  }
}

// --- TAREFA DE SENSORES E MOTORES ---
void sensor_motor_task(void *pvParameters) {
  char localRobotState;
  TelemetryData dataToSend;
  sensors_event_t a, g, temp;
  float pitch_acc, roll_acc;

  // --- Variáveis para média móvel dos encoders ---
  const int MOVING_AVG_SIZE = 5;
  int16_t readings_A[MOVING_AVG_SIZE] = {0}; long total_A = 0; int index_A = 0;
  int16_t readings_B[MOVING_AVG_SIZE] = {0}; long total_B = 0; int index_B = 0;

  // --- Variáveis para média móvel da bateria ---
  const int BATT_AVG_SIZE = 10;
  uint16_t readings_batt[BATT_AVG_SIZE] = {0};
  long total_batt = 0;
  int index_batt = 0;

  last_filter_time = micros();

  for (;;) {
    // --- Leitura de sensores e encoders ---
    int16_t raw_counts_A, raw_counts_B;
    pcnt_get_counter_value(PCNT_UNIT_0, &raw_counts_A);
    pcnt_get_counter_value(PCNT_UNIT_1, &raw_counts_B);
    pcnt_counter_clear(PCNT_UNIT_0);
    pcnt_counter_clear(PCNT_UNIT_1);

    mpu.getEvent(&a, &g, &temp);
    uint16_t adc_value = analogRead(batteryPin);
    
    // --- Lógica do filtro complementar ---
    unsigned long current_time = micros();
    float dt = (current_time - last_filter_time) / 1000000.0;
    last_filter_time = current_time;
    pitch_acc = atan2(-a.acceleration.x, sqrt(a.acceleration.y * a.acceleration.y + a.acceleration.z * a.acceleration.z)) * RAD_TO_DEG;
    roll_acc  = atan2(a.acceleration.y, a.acceleration.z) * RAD_TO_DEG;
    float gyro_pitch = g.gyro.y * RAD_TO_DEG;
    float gyro_roll = g.gyro.x * RAD_TO_DEG;
    anglePitch = ALPHA * (anglePitch + gyro_pitch * dt) + (1 - ALPHA) * pitch_acc;
    angleRoll  = ALPHA * (angleRoll + gyro_roll * dt) + (1 - ALPHA) * roll_acc;

    // --- Preenchimento da struct de telemetria ---
    dataToSend.timestamp_us = esp_timer_get_time();
    dataToSend.pitch = anglePitch;
    dataToSend.roll = angleRoll;
    dataToSend.gyro_z_raw = g.gyro.z;
    
    // --- Média móvel dos encoders (usando int32_t) ---
    total_A = total_A - readings_A[index_A] + raw_counts_A;
    readings_A[index_A] = raw_counts_A;
    index_A = (index_A + 1) % MOVING_AVG_SIZE;
    dataToSend.left_encoder = total_A / MOVING_AVG_SIZE;

    total_B = total_B - readings_B[index_B] + raw_counts_B;
    readings_B[index_B] = raw_counts_B;
    index_B = (index_B + 1) % MOVING_AVG_SIZE;
    dataToSend.right_encoder = total_B / MOVING_AVG_SIZE;

    // --- Cálculo da tensão da bateria em mV ---
    float voltage_at_pin_mv = (adc_value / 4095.0) * 3300.0;
    uint16_t current_battery_mv = (uint16_t)(voltage_at_pin_mv * VOLTAGE_DIVIDER_FACTOR);
    total_batt = total_batt - readings_batt[index_batt] + current_battery_mv;
    readings_batt[index_batt] = current_battery_mv;
    index_batt = (index_batt + 1) % BATT_AVG_SIZE;
    dataToSend.battery_mv = total_batt / BATT_AVG_SIZE;

    // --- CÁLCULO DO CHECKSUM ---
    uint8_t* data_ptr = (uint8_t*)&dataToSend; // Ponteiro para o início da struct
    uint8_t checksum = 0;
    // Itera por todos os bytes da struct, exceto o último (que é o próprio checksum)
    for (int i = 0; i < sizeof(TelemetryData) - 1; i++) {
        checksum ^= data_ptr[i]; // Operação XOR
    }
    dataToSend.checksum = checksum; // Armazena o checksum calculado

    // Envia os dados para a fila, para serem lidos pela communication_task
    xQueueSend(telemetryQueue, &dataToSend, (TickType_t) 0);

    // --- Controle dos motores ---
    if (xSemaphoreTake(commandMutex, (TickType_t) 10) == pdTRUE) {
      localRobotState = robotState;
      xSemaphoreGive(commandMutex);
    }

    switch (localRobotState) {
      case 'F': moveForward(); break;
      case 'B': moveBackward(); break;
      case 'L': turnLeft(); break;
      case 'R': turnRight(); break;
      case 'S': stopMotors(); break;
      default: stopMotors(); break;
    }

    vTaskDelay(pdMS_TO_TICKS(10));
    
  }

}