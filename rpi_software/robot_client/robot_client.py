import serial
import struct
import json
import time
import logging
import sys
from functools import reduce
from logging.handlers import RotatingFileHandler
import paho.mqtt.client as mqtt

# --- 1. CONFIGURAÇÃO DO LOGGER ---
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

# --- 2. CONFIGURAÇÕES GERAIS ---
# MQTT
BROKER_ADDRESS = "littlegreycell.local" 
PORT = 1883
TOPIC_TELEMETRY_IMU = "robot/tele/imu"
TOPIC_TELEMETRY_BATTERY = "robot/tele/battery"
TOPIC_TELEMETRY_ENCODERS = "robot/tele/encoders"
TOPIC_COMMAND_DRIVE = "robot/cmnd/drive"

# SERIAL
SERIAL_PORT = '/dev/ttyS0' 
BAUD_RATE = 115200 
SOP = b'\xAA\x55' # Start of Packet
STRUCT_FORMAT = '<qffhiihB'
STRUCT_SIZE = struct.calcsize(STRUCT_FORMAT)

# --- 3. CLASSE PARA GERENCIAR A COMUNICAÇÃO SERIAL ---
class SerialHandler:
    def __init__(self, port, baudrate):
        self.ser = None
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            logger.info(f"Porta serial {port} aberta com sucesso.")
        except serial.SerialException as e:
            logger.error(f"Falha ao abrir a porta serial {port}: {e}")
            sys.exit(1)

    def read_telemetry_packet(self):
        # Procura pelo marcador de início de pacote
        byte1 = self.ser.read(1)
        if not byte1 or byte1 != SOP[0:1]: return None
        byte2 = self.ser.read(1)
        if not byte2 or byte2 != SOP[1:2]: return None
        
        # Lê o pacote de dados
        packet_buffer = self.ser.read(STRUCT_SIZE)
        
        if len(packet_buffer) == STRUCT_SIZE:
            # Valida o checksum
            data_bytes = packet_buffer[:-1]
            received_checksum = packet_buffer[-1]
            calculated_checksum = reduce(lambda x, y: x ^ y, data_bytes)

            if received_checksum == calculated_checksum:
                # Desempacota e retorna os dados
                return struct.unpack(STRUCT_FORMAT, packet_buffer)
            else:
                logger.warning(f"Checksum inválido! Recebido: {received_checksum}, Calculado: {calculated_checksum}")
                return None
        return None

    def send_drive_command(self, left_speed, right_speed):
        command = f"DRIVE:{int(left_speed)},{int(right_speed)}\n"
        self.ser.write(command.encode('utf-8'))
        logger.info(f"Comando enviado para o ESP32: {command.strip()}")
        
    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.write(b"DRIVE:0,0\n") # Comando de segurança ao fechar
            self.ser.close()
            logger.info("Porta serial fechada.")

# --- 4. CALLBACKS MQTT ---
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        logger.warning(f"Falha ao conectar ao broker: {reason_code}")
    else:
        logger.info("Conectado com sucesso ao Broker MQTT.")
        logger.info(f"Inscrevendo-se no tópico de comandos: {TOPIC_COMMAND_DRIVE}")
        client.subscribe(TOPIC_COMMAND_DRIVE)

def on_message(client, userdata, msg):
    """Callback para quando um comando é recebido via MQTT."""
    serial_handler = userdata['serial_handler']
    
    try:
        payload = msg.payload.decode()
        logger.info(f"Comando MQTT recebido | Tópico: '{msg.topic}' | Payload: {payload}")
        
        data = json.loads(payload)
        left = data.get('left', 0)
        right = data.get('right', 0)
        
        serial_handler.send_drive_command(left, right)
        
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON do payload: {msg.payload}")
    except Exception as e:
        logger.error(f"Erro ao processar mensagem MQTT: {e}")

def on_disconnect(client, userdata, flags, reason_code, properties):
    logger.warning(f"Desconectado do broker! Motivo: {reason_code}")

# --- 5. LÓGICA PRINCIPAL ---
if __name__ == "__main__":
    logger.info("Iniciando cliente do robô (ponte Serial-MQTT)...")

    # Inicializa o handler da serial
    serial_handler = SerialHandler(SERIAL_PORT, BAUD_RATE)
    
    # Inicializa o cliente MQTT e passa o handler da serial para os callbacks
    user_data = {'serial_handler': serial_handler}
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=user_data)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        client.connect(BROKER_ADDRESS, PORT, 60)
        client.loop_start() # Inicia o loop MQTT em uma thread separada

        while True:
            # O loop principal agora lê da serial e publica no MQTT
            telemetry_data = serial_handler.read_telemetry_packet()
            
            if telemetry_data:
                # Desempacota os dados com nomes claros
                (timestamp, pitch, roll, gyro_z, 
                 enc_l, enc_r, battery_mv, checksum) = telemetry_data

                # Cria e publica os payloads JSON
                imu_payload = json.dumps({"pitch": round(pitch, 2), "roll": round(roll, 2), "gyro_z": gyro_z})
                battery_payload = json.dumps({"voltage_mv": battery_mv})
                encoders_payload = json.dumps({"left": enc_l, "right": enc_r, "timestamp_us": timestamp})
                
                client.publish(TOPIC_TELEMETRY_IMU, imu_payload)
                client.publish(TOPIC_TELEMETRY_BATTERY, battery_payload)
                client.publish(TOPIC_TELEMETRY_ENCODERS, encoders_payload)
                
                logger.debug(f"Telemetria publicada: Bat:{battery_mv}mV, Pitch:{pitch:.1f}, Roll:{roll:.1f}")
            
            time.sleep(0.005)

    except KeyboardInterrupt:
        logger.info("Sinal de interrupção recebido. Desligando...")
    except Exception as e:
        logger.critical(f"Erro fatal na thread principal: {e}")
    finally:
        logger.info("Encerrando conexões...")
        client.loop_stop()
        client.disconnect()
        serial_handler.close()
        logger.info("Cliente do robô encerrado.")