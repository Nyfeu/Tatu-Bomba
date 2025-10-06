# config.py
# Ficheiro central para todas as configurações da aplicação.

# --- CONFIGURAÇÕES MQTT ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_COMMAND_DRIVE = "robot/cmnd/drive"
TOPIC_TELEMETRY = "robot/tele/#"

# --- CONFIGURAÇÕES DE VÍDEO ---
# Altere para o endereço IP do seu Raspberry Pi ou use .local se o mDNS estiver configurado.
VIDEO_URL = "http://pizero.local:8000/stream.mjpg"
MIN_VOLTAGE = 6.0  # Voltagem mínima para o indicador de bateria
MAX_VOLTAGE = 8.4  # Voltagem máxima para o indicador de bateria
