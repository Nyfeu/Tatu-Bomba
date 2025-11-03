import paho.mqtt.client as mqtt
import json
import time
import logging
import math

# --- 1. CONFIGURAÇÃO (Coprada do robot_client.py) ---
# Altere para o IP do seu broker se não estiver rodando localmente
BROKER_ADDRESS = "localhost" 
PORT = 1883
TOPIC_TELEMETRY_IMU = "robot/tele/imu"
TOPIC_TELEMETRY_BATTERY = "robot/tele/battery"
TOPIC_TELEMETRY_ENCODERS = "robot/tele/encoders"

# --- 2. CONFIGURAÇÃO DO LOGGER ---
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
logger = logging.getLogger("RobotSimulator")
logger.setLevel(logging.INFO)
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

# --- 3. CALLBACKS MQTT ---
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        logger.warning(f"Falha ao conectar ao broker: {reason_code}")
    else:
        logger.info("Conectado com sucesso ao Broker MQTT.")
        logger.info("Iniciando simulação de telemetria...")

def on_disconnect(client, userdata, flags, reason_code, properties):
    logger.warning(f"Desconectado do broker! Motivo: {reason_code}")

# --- 4. LÓGICA PRINCIPAL DA SIMULAÇÃO ---
if __name__ == "__main__":
    logger.info("Iniciando simulador de telemetria do robô...")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    try:
        client.connect(BROKER_ADDRESS, PORT, 60)
        client.loop_start()

        # Variáveis para simulação
        angle = 0
        battery_mv = 12600  # Começa em 12.6V (12600mV)
        battery_direction = -1
        encoder_count = 0

        while True:
            # --- Simula o Yaw (gyro_z) ---
            # Faz o robô girar lentamente 360 graus
            angle = (angle + 1) % 360

            # --- Simula a Bateria (voltage_mv) ---
            # Varia a voltagem entre 6.0V (6000mV) e 12.6V (12600mV)
            battery_mv += battery_direction * 20  # Altera em 20mV por ciclo
            if battery_mv >= 12600:
                battery_direction = -1
            elif battery_mv <= 6000:
                battery_direction = 1

            # --- Simula Pitch e Roll ---
            # Usa senos/cossenos para fazer o horizonte artificial se mover
            pitch = 15 * math.sin(math.radians(angle * 2))
            roll = 25 * math.cos(math.radians(angle))

            # --- Simula Encoders (MODIFICADO) ---
            # Faz o contador variar de 0 a 10 (em passos de 1) e depois reiniciar
            encoder_count = (encoder_count + 1) % 11 
            # (Usa 105 para que o último valor seja 100 antes de voltar a 0)
            
            timestamp = int(time.time() * 100)

            # --- Cria os Payloads (exatamente como o robot_client.py) ---
            
            # 1. IMU (Testa o gyro_z)
            imu_payload = json.dumps({
                "pitch": round(pitch, 2), 
                "roll": round(roll, 2), 
                "gyro_z": angle  # <-- O dashboard deve ler isso como "yaw"
            })
            
            # 2. Bateria (Testa o voltage_mv)
            battery_payload = json.dumps({
                "voltage_mv": battery_mv # <-- O dashboard deve ler e converter para V
            })
            
            # 3. Encoders (Apenas para completar)
            encoders_payload = json.dumps({
                "left": encoder_count, 
                "right": int(encoder_count * 0.9), # Um pouco diferente
                "timestamp_us": timestamp
            })

            # --- Publica os dados ---
            client.publish(TOPIC_TELEMETRY_IMU, imu_payload)
            client.publish(TOPIC_TELEMETRY_BATTERY, battery_payload)
            client.publish(TOPIC_TELEMETRY_ENCODERS, encoders_payload)
            
            logger.info(f"Publicado: Batt: {battery_mv}mV, Yaw (gyro_z): {angle}, Enc: {encoder_count}")
            
            # Atualiza 20 vezes por segundo (50ms)
            time.sleep(0.05) 

    except KeyboardInterrupt:
        logger.info("Simulação interrompida. Desligando...")
    except Exception as e:
        logger.critical(f"Erro fatal na simulação: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        logger.info("Simulador encerrado.")