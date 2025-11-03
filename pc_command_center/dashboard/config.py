# --- CONFIGURAÇÕES MQTT ---
MQTT_BROKER = "localhost"                                     # Endereço do broker MQTT
MQTT_PORT = 1883                                              # Porta padrão do MQTT
TOPIC_COMMAND_DRIVE = "robot/cmnd/drive"                      # Tópico para comandos de direção
TOPIC_TELEMETRY = "robot/tele/#"                              # Inscreve-se em todos os tópicos de telemetria

# --- CONFIGURAÇÕES DE VÍDEO ---
VIDEO_URL = "http://pizero.local:8000/stream.mjpg"            # URL do stream de vídeo MJPEG do Raspberry Pi Zero
MIN_VOLTAGE = 6.0                                             # Tensão elétrica (V) mínima para o indicador de bateria
MAX_VOLTAGE = 12.6                                            # Voltagem máxima para o indicador de bateria

# --- CONFIGURAÇÕES PARA VELOCIDADE DO ROBÔ ---
ENCODER_PPR = 20                                              # Pulsos por revolução do encoder
ENCODER_INTERVAL_S = 0.1                                      # Intervalo de tempo entre leituras dos encoders em segundos
ENCODER_TO_RPM_K = (60 / (ENCODER_PPR * ENCODER_INTERVAL_S))  # Fator de conversão de pulsos do encoder para RPM
SPEEDOMETER_MAX_RPM = 150                                     # RPM máxima exibida no velocímetro