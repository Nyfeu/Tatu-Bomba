#include "motors.h"
#include "globals.h"
#include "config.h"

void setupMotors() {
    pinMode(in1, OUTPUT);
    pinMode(in2, OUTPUT);
    pinMode(in3, OUTPUT);
    pinMode(in4, OUTPUT);
    ledcSetup(pwmChannelA, freq, resolution);
    ledcSetup(pwmChannelB, freq, resolution);
    ledcAttachPin(enA, pwmChannelA);
    ledcAttachPin(enB, pwmChannelB);
    stopMotors();
    DEBUG_PRINTLN("Motores inicializados.");
}

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

  // Cria uma variável local para a velocidade atual para não modificar a global
  int currentSpeed = motorSpeed;

  // Rampa de desaceleração
  for (int i = currentSpeed; i >= 0; i--) {
      ledcWrite(pwmChannelA, i);
      ledcWrite(pwmChannelB, i);
      delay(DECCEL_DELAY);
  }

  // Garante que os motores parem completamente 
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  ledcWrite(pwmChannelA, 0);
  ledcWrite(pwmChannelB, 0);

}