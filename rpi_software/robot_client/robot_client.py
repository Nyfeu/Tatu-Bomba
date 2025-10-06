import paho.mqtt.client as mqtt
import time
import json
import random
import logging
import sys
from logging.handlers import RotatingFileHandler

# --- 1. CONFIGURACAO DO LOGGER ---
# (A configuracao do logger permanece a mesma)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
logger = logging.getLogger("RobotClient")
logger.setLevel(logging.INFO)
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)
    file_handler = RotatingFileHandler('robot_client.log', maxBytes=5*1024*1024, backupCount=2)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

# --- CONFIGURACOES ---
BROKER_ADDRESS = "littlegreycell.local" 
PORT = 1883
TOPIC_TELEMETRY_BATTERY = "robot/tele/battery"
TOPIC_TELEMETRY_IMU = "robot/tele/imu"
TOPIC_COMMAND_DRIVE = "robot/cmnd/drive"

# --- VARIAVEL GLOBAL DE ESTADO DA CONEXAO ---
client_connected = False

# --- CALLBACKS MQTT ---
def on_connect(client, userdata, flags, reason_code, properties):
    """Callback chamado quando a conexao e estabelecida."""
    global client_connected
    if reason_code.is_failure:
        # A mensagem de erro agora e um aviso, pois vamos tentar reconectar.
        logger.warning(f"Falha ao conectar ao broker: {reason_code}")
        client_connected = False
    else:
        # Limpa a linha da animacao e imprime a mensagem de sucesso
        print("\n" + " " * 80, end="\r") 
        logger.info("Conectado com sucesso ao Broker MQTT.")
        logger.info(f"Inscrevendo-se no topico de comandos: {TOPIC_COMMAND_DRIVE}")
        client.subscribe(TOPIC_COMMAND_DRIVE)
        client_connected = True

def on_message(client, userdata, msg):
    """Callback para recebimento de mensagens."""
    logger.info(f"Comando recebido | Topico: '{msg.topic}' | Payload: {msg.payload.decode()}")

def on_disconnect(client, userdata, flags, reason_code, properties):
    """Callback chamado quando o cliente se desconecta."""
    global client_connected
    logger.warning(f"Desconectado do broker! Motivo: {reason_code}")
    client_connected = False

# --- LOGICA PRINCIPAL ---
logger.info("Iniciando cliente do robo...")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Tenta a conexao inicial de forma nao bloqueante
client.connect_async(BROKER_ADDRESS, PORT, 60)
client.loop_start()

animation_states = ["   ", ".  ", ".. ", "..."]
animation_index = 0

try:
    while True:
        if client_connected:
            # Se conectado, publica a telemetria
            battery_voltage = round(random.uniform(7.0, 8.4), 2)
            imu_data = {
                "pitch": round(random.uniform(-5.0, 5.0), 2),
                "roll": round(random.uniform(-5.0, 5.0), 2),
                "yaw": round(random.uniform(0.0, 360.0), 2)
            }
            battery_payload = json.dumps({"voltage": battery_voltage})
            imu_payload = json.dumps(imu_data)

            logger.info(f"Publicando telemetria: Bateria={battery_payload}, IMU={imu_payload}")
            
            client.publish(TOPIC_TELEMETRY_BATTERY, battery_payload)
            client.publish(TOPIC_TELEMETRY_IMU, imu_payload)
            
            time.sleep(2)
        else:
            # Se nao conectado, exibe a animacao de espera
            # O loop em segundo plano do paho-mqtt ja esta a tratar da reconexao.
            message = f"Aguardando conexao com Mosquitto (Broker MQTT){animation_states[animation_index]}"
            
            # Usa sys.stdout para escrever na mesma linha
            sys.stdout.write(message + '\r')
            sys.stdout.flush()
            
            animation_index = (animation_index + 1) % len(animation_states)
            time.sleep(0.5)

except KeyboardInterrupt:
    logger.info("Sinal de interrupcao recebido. Desligando...")
finally:
    client.loop_stop()
    client.disconnect()
    print("\n" + " " * 80, end="\r") # Limpa a linha final
    logger.info("Cliente do robo encerrado.")

