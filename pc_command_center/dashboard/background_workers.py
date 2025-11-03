import cv2
import numpy as np
import logging
import time

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

import config
from mqtt_client import MqttClientHandler

logger = logging.getLogger(__name__)

# --- WORKER PARA O CLIENTE MQTT ---
class MqttWorker(QObject):
    telemetry_received = pyqtSignal(str, str)
    connection_status = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.mqtt_handler = MqttClientHandler(config.MQTT_BROKER, config.MQTT_PORT)
        self.mqtt_handler.add_external_on_message_callback(self._handle_incoming_message)
        self.mqtt_handler.add_external_on_connect_callback(self._handle_connection_result)
        self.mqtt_handler.client.on_disconnect = self._handle_disconnection

    @pyqtSlot()
    def run(self):
        """
        Inicia o cliente MQTT. A biblioteca paho-mqtt ja lida com a reconexao
        automatica quando usamos loop_start().
        """
        logger.info("Thread MQTT iniciada.")
        self.connection_status.emit("Conectando...")
        self.mqtt_handler.connect()

    def _handle_connection_result(self, rc):
        if rc == 0:
            logger.info("Conexao MQTT confirmada. Inscrevendo-se na telemetria.")
            self.mqtt_handler.subscribe(config.TOPIC_TELEMETRY)
            self.connection_status.emit("Conectado")
        else:
            logger.error(f"Falha na conexao MQTT confirmada com o codigo: {rc}")
            self.connection_status.emit("Falha na conexao")

    def _handle_disconnection(self, client, userdata, rc):
        """Callback interno que atualiza a UI quando a conexao cai."""
        logger.warning("Conexao com o broker perdida. A biblioteca tentara reconectar...")
        self.connection_status.emit("Reconectando...")

    def _handle_incoming_message(self, topic, payload):
        self.telemetry_received.emit(topic, payload)

    @pyqtSlot(str, str)
    def publish_command(self, topic, payload):
        if not self.mqtt_handler.publish(topic, payload):
            logger.warning("Falha ao enviar comando via MQTT (nao conectado).")

    @pyqtSlot()
    def stop(self):
        """Sinaliza ao handler para parar."""
        logger.info("Thread MQTT a encerrar...")
        self.mqtt_handler.disconnect()

# --- WORKER PARA O STREAM DE VIDEO ---
class VideoWorker(QObject):
    new_frame = pyqtSignal(np.ndarray)
    video_status = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._is_running = True

    @pyqtSlot()
    def run(self):
        logger.info("Thread de video iniciada.")
        while self._is_running:
            logger.info(f"Tentando conectar ao stream de video em {config.VIDEO_URL}...")
            self.video_status.emit("Conectando...")
            cap = cv2.VideoCapture(config.VIDEO_URL)
            
            if not cap.isOpened():
                self.video_status.emit("Aguardando...")
                QThread.sleep(5) 
                continue
            
            self.video_status.emit("Conectado")
            
            while self._is_running:
                ret, frame = cap.read()
                if ret and self._is_running:
                    self.new_frame.emit(frame)
                elif not ret:
                    logger.warning("Stream de video perdido. Tentando reconectar...")
                    self.video_status.emit("Reconectando...")
                    QThread.msleep(1000)
                    break 
            
            cap.release()
        
        logger.info("Thread de video encerrada.")

    @pyqtSlot()
    def stop(self):
        self._is_running = False

