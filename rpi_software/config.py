# Arquivo de configuracao para o software da Raspberry Pi.

# --- Configuracoes de Comunicacao ----------------------------------

# Endereco do Broker MQTT. Usa o nome .local (mDNS) ou o IP do PC
MQTT_BROKER = "littlegreycell.local" 
MQTT_PORT = 1883

# Porta Serial para comunicacao com o ESP32
# No RPi Zero 2W é '/dev/ttyS0'
SERIAL_PORT = '/dev/ttyS0'
SERIAL_BAUD_RATE = 115200

# --- Configuracoes do Robo -----------------------------------------

# (Estes parametros serao usados pelo EKF no futuro)
WHEEL_RADIUS = 0.075 # Raio da roda em metros (150 mm diâmetro)

# -------------------------------------------------------------------