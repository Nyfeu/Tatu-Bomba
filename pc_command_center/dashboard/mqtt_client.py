import paho.mqtt.client as mqtt
import logging

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

        self.client_connected = False
        self.external_on_message = None
        self.external_on_connect = None

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.client_connected = True
            logger.info(f"Conectado ao broker MQTT em {self.broker_ip}")
            if self.external_on_connect:
                self.external_on_connect(rc)
        else:
            self.client_connected = False
            logger.error(f"Falha ao conectar ao broker, codigo de retorno: {rc}")
            if self.external_on_connect:
                self.external_on_connect(rc)

    def _on_disconnect(self, client, userdata, rc):
        self.client_connected = False
        logger.warning(f"Desconectado do broker com codigo: {rc}")

    def _on_message(self, client, userdata, msg):
        if self.external_on_message:
            self.external_on_message(msg.topic, msg.payload.decode())

    def add_external_on_message_callback(self, callback):
        self.external_on_message = callback

    def add_external_on_connect_callback(self, callback):
        self.external_on_connect = callback

    def is_connected(self):
        """Retorna o status atual da conexao."""
        return self.client_connected

    def connect(self):
        try:
            logger.info(f"MqttClientHandler: Tentando conectar a {self.broker_ip}:{self.port}...")
            self.client.connect(self.broker_ip, self.port, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"MqttClientHandler: Excecao ao tentar conectar: {e}")
            return False

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MqttClientHandler: Desconectado.")

    def subscribe(self, topic):
        self.client.subscribe(topic)
        logger.info(f"Inscrito no topico: {topic}")

    def publish(self, topic, payload):
        if self.client_connected:
            result = self.client.publish(topic, payload)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                return True
        return False

