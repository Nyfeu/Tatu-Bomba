# Arquivo de configuracao para o software da Raspberry Pi.

# --- Configuracoes de Comunicacao ----------------------------------

# Endereco do Broker MQTT. Usa o nome .local (mDNS) do PC
MQTT_BROKER = "littlegreycell.local" 
MQTT_PORT = 1883

# Porta Serial para comunicacao com o ESP32
# No RPi Zero 2W é '/dev/ttyS0'
SERIAL_PORT = '/dev/ttyS0'
SERIAL_BAUD_RATE = 115200
