import paho.mqtt.client as mqtt
import logging

# Configura um logger específico para este módulo
logger = logging.getLogger(__name__)

class MqttClientHandler:
    def __init__(self, broker_ip, port, client_id=None):
        self.broker_ip = broker_ip
        self.port = port
        self.client_id = client_id
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        self.external_on_message_callback = None
        self.external_on_connect_callback = None # Novo callback para status de conexão

    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback interno que é chamado pela biblioteca paho-mqtt.
        Ele então notifica o código externo através do callback registrado.
        """
        if rc == 0:
            logger.info("MqttClientHandler: Conexão com o broker confirmada (rc=0).")
        else:
            logger.error(f"MqttClientHandler: Falha ao conectar, código: {rc}")
        
        if self.external_on_connect_callback:
            self.external_on_connect_callback(rc)

    def _on_message(self, client, userdata, msg):
        logger.debug(f"MqttClientHandler: Mensagem recebida no tópico '{msg.topic}'")
        if self.external_on_message_callback:
            self.external_on_message_callback(msg.topic, msg.payload.decode())

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning("MqttClientHandler: Desconexão inesperada do broker.")
        else:
            logger.info("MqttClientHandler: Desconectado de forma limpa.")

    def add_external_on_message_callback(self, callback_func):
        self.external_on_message_callback = callback_func

    def add_external_on_connect_callback(self, callback_func):
        """Permite registrar uma função para ser notificada do resultado da conexão."""
        self.external_on_connect_callback = callback_func

    def connect(self):
        """Apenas inicia a tentativa de conexão. Não retorna o status."""
        try:
            logger.info(f"MqttClientHandler: Tentando conectar a {self.broker_ip}:{self.port}...")
            self.client.connect(self.broker_ip, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.critical(f"MqttClientHandler: Exceção ao tentar conectar: {e}")
            # Notifica imediatamente sobre a falha se ocorrer uma exceção
            if self.external_on_connect_callback:
                self.external_on_connect_callback(-1) # -1 como código de erro customizado

    def subscribe(self, topic):
        logger.info(f"MqttClientHandler: Inscrevendo-se no tópico '{topic}'")
        self.client.subscribe(topic)

    def publish(self, topic, payload):
        if self.client.is_connected():
            result = self.client.publish(topic, payload)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"MqttClientHandler: Erro ao enfileirar mensagem: {mqtt.error_string(result.rc)}")
                return False
            return True
        else:
            logger.warning("MqttClientHandler: Cliente não está conectado. Publicação falhou.")
            return False

    def disconnect(self):
        logger.info("MqttClientHandler: Solicitando desconexão...")
        self.client.loop_stop()
        self.client.disconnect()

