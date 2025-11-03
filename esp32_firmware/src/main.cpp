#include "globals.h"
#include "sensors.h"
#include "motors.h"
#include "tasks.h"

void setup() {
  delay(1000);

  // Inicia a porta Serial padrão (USB) para mensagens de DEBUG
  Serial.begin(115200);

  // Inicia a porta de comunicação correta baseada na configuração
  #if USE_USB_SERIAL
    DEBUG_PRINTLN("MODO DEBUG: Usando a porta USB Serial para comandos e telemetria.");
  #else
    SerialRPi.begin(115200, SERIAL_8N1, RPI_RX_PIN, RPI_TX_PIN);
    DEBUG_PRINTLN("MODO PRODUÇÃO: Usando a porta UART para comunicação com a Raspberry Pi.");
  #endif
  
  Wire.begin(sda_pin, scl_pin, 400000);
  
  // Inicializa os subsistemas
  setupMPU();
  setupEncoders();
  setupMotors();
  setupADC();
  
  // --- CRIAÇÃO DOS ELEMENTOS FREERTOS --- 
  telemetryQueue = xQueueCreate(5, sizeof(TelemetryData)); 
  commandMutex = xSemaphoreCreateMutex();

  // --- CRIAÇÃO DAS TAREFAS ---
  xTaskCreate(communication_task, "CommTask", 4096, NULL, 1, &communicationTaskHandle);
  xTaskCreate(sensor_motor_task, "SensorMotorTask", 4096, NULL, 2, &sensorMotorTaskHandle);
  
  DEBUG_PRINTLN("Setup concluído. Tarefas criadas.");
}

void loop() {
  vTaskDelete(NULL);
}