import json
import logging
import math
import cv2
import numpy as np

from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QGridLayout
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot, Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap

import config
from ui_widgets import (ArtificialHorizonWidget, SpeedometerWidget, HorizontalCompassWidget,
                        MapContainerWidget, KeyIndicatorWidget, TopLeftInfoWidget,
                        RawTelemetryWidget)
from background_workers import MqttWorker, VideoWorker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    command_signal = pyqtSignal(str, str)
    stop_workers_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robot Control HUD")
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet("""
            QMainWindow { background-color: #000; }
            #video_label { background-color: #0d1b2a; }
        """)

        self.keys_pressed = set()
        self.last_drive_payload = None
        self.robot_pose = {'x': 0.0, 'y': 0.0, 'angle': 0.0}
        self.telemetry_state = {}

        self.setup_ui_hud()
        self.setup_threads()
        
        self.simulation_timer = QTimer(self)
        self.simulation_timer.timeout.connect(self.update_simulation)
        self.simulation_timer.start(50)

    def setup_ui_hud(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.main_layout = QGridLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(20)

        self.video_label = QLabel("Awaiting Video Stream...")
        self.video_label.setObjectName("video_label")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.main_layout.addWidget(self.video_label, 0, 0, 1, 1)

        hud_widget = QWidget()
        hud_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hud_layout = QGridLayout(hud_widget)
        self.hud_layout.setContentsMargins(20, 20, 20, 20)
        self.hud_layout.setSpacing(10)

        self.info_widget = TopLeftInfoWidget()
        self.compass_widget = HorizontalCompassWidget()
        # --- Usa o novo MapContainerWidget ---
        self.map_container = MapContainerWidget()
        self.map_container.setFixedSize(300, 300)
        
        self.speedometer_widget = SpeedometerWidget()
        self.key_indicator = KeyIndicatorWidget()
        self.horizon_widget = ArtificialHorizonWidget()
        self.telemetry_widget = RawTelemetryWidget()

        
        self.hud_layout.addWidget(self.info_widget, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.hud_layout.addWidget(self.telemetry_widget, 1, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.hud_layout.addWidget(self.compass_widget, 0, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.hud_layout.addWidget(self.map_container, 0, 2, 2, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        self.hud_layout.addWidget(self.speedometer_widget, 2, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        self.hud_layout.addWidget(self.key_indicator, 2, 1, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.hud_layout.addWidget(self.horizon_widget, 2, 2, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

        self.main_layout.addWidget(hud_widget, 0, 0, 1, 1)

    def setup_threads(self):
        # MQTT
        self.mqtt_thread = QThread()
        self.mqtt_worker = MqttWorker()
        self.mqtt_worker.moveToThread(self.mqtt_thread)
        self.mqtt_thread.started.connect(self.mqtt_worker.run)
        self.mqtt_worker.telemetry_received.connect(self.update_telemetry)
        self.mqtt_worker.connection_status.connect(self.info_widget.set_mqtt_status)
        self.command_signal.connect(self.mqtt_worker.publish_command)
        self.stop_workers_signal.connect(self.mqtt_worker.stop)
        self.mqtt_thread.start()

        # Vídeo
        self.video_thread = QThread()
        self.video_worker = VideoWorker()
        self.video_worker.moveToThread(self.video_thread)
        self.video_thread.started.connect(self.video_worker.run)
        self.video_worker.new_frame.connect(self.update_video_frame)
        self.video_worker.video_status.connect(self.info_widget.set_video_status)
        self.stop_workers_signal.connect(self.video_worker.stop)
        self.video_thread.start()
        
        # Conecta o sinal do botão de reset
        self.map_container.map_widget.reset_map_signal.connect(self.on_reset_map)


    @pyqtSlot()
    def update_simulation(self):
        linear_speed = 50.0
        angular_speed = 90.0
        dt = 0.050

        throttle, turn = 0, 0
        if 'W' in self.keys_pressed: throttle = 1
        elif 'S' in self.keys_pressed: throttle = -1
        if 'A' in self.keys_pressed: turn = -1  
        elif 'D' in self.keys_pressed: turn = 1
        
        if throttle != 0 or turn != 0:
            self.robot_pose['angle'] += turn * angular_speed * dt
            angle_rad = math.radians(self.robot_pose['angle'])
            distance = throttle * linear_speed * dt
            self.robot_pose['x'] += distance * math.cos(angle_rad)
            self.robot_pose['y'] += distance * math.sin(angle_rad)
            self.map_container.map_widget.add_path_point(self.robot_pose['x'], self.robot_pose['y'])
        
        self.map_container.map_widget.update_robot_pose(self.robot_pose['x'], self.robot_pose['y'], self.robot_pose['angle'])

    @pyqtSlot()
    def on_reset_map(self):
        logger.info("Resetando o mapa e a odometria simulada.")
        self.robot_pose = {'x': 0.0, 'y': 0.0, 'angle': 0.0}
        self.map_container.map_widget.reset_map()


    def send_movement_command(self):
        base_speed, turn_speed = 80, 70
        throttle, turn = 0, 0
        if 'W' in self.keys_pressed: throttle = base_speed
        elif 'S' in self.keys_pressed: throttle = -base_speed
        if 'A' in self.keys_pressed: turn = -turn_speed
        elif 'D' in self.keys_pressed: turn = turn_speed
            
        left_speed = max(-100, min(100, throttle + turn))
        right_speed = max(-100, min(100, throttle - turn))
        
        drive_payload = {"left": int(left_speed), "right": int(right_speed)}
        
        if drive_payload != self.last_drive_payload:
            self.command_signal.emit(config.TOPIC_COMMAND_DRIVE, json.dumps(drive_payload))
            self.last_drive_payload = drive_payload

    def keyPressEvent(self, event):
        if event.isAutoRepeat(): return
        key_map = {Qt.Key.Key_W: 'W', Qt.Key.Key_A: 'A', Qt.Key.Key_S: 'S', Qt.Key.Key_D: 'D'}
        if event.key() in key_map:
            self.keys_pressed.add(key_map[event.key()])
            self.key_indicator.update_keys(self.keys_pressed)
            self.send_movement_command()

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat(): return
        key_map = {Qt.Key.Key_W: 'W', Qt.Key.Key_A: 'A', Qt.Key.Key_S: 'S', Qt.Key.Key_D: 'D'}
        if event.key() in key_map and key_map[event.key()] in self.keys_pressed:
            self.keys_pressed.remove(key_map[event.key()])
            self.key_indicator.update_keys(self.keys_pressed)
            self.send_movement_command()

    @pyqtSlot(str, str)
    def update_telemetry(self, topic, payload):
        try:

            key = topic.split('/')[-1]
            if key == '#':
                key = topic.split('/')[-2]

            data = json.loads(payload)

            self.telemetry_state[key] = data

            full_telemetry_str = json.dumps(self.telemetry_state, indent=2)
            self.telemetry_widget.update_telemetry(full_telemetry_str)

            if key == "battery":
                voltage_mv = data.get('voltage_mv', 0.0)
                voltage_v = voltage_mv / 1000.0
                min_v, max_v = config.MIN_VOLTAGE, config.MAX_VOLTAGE
                percent = int(100 * (voltage_v - min_v) / (max_v - min_v))
                percent = max(0, min(100, percent))
                self.info_widget.set_battery_value(voltage_v, percent)

            elif key == "imu":
                pitch = data.get('pitch', 0.0)
                roll = data.get('roll', 0.0)
                yaw = data.get('gyro_z', 0.0)
                self.horizon_widget.set_angles(pitch, roll)
                self.compass_widget.set_heading(yaw)

            elif key == "encoders":
                enc_l = data.get('left', 0)
                enc_r = data.get('right', 0)
                
                rpm_l = enc_l * config.ENCODER_TO_RPM_K
                rpm_r = enc_r * config.ENCODER_TO_RPM_K

                robot_speed_rpm = (rpm_l + rpm_r) / 2.0
                
                self.speedometer_widget.set_speed(abs(robot_speed_rpm))

        except (json.JSONDecodeError, IndexError):
            pass 
        except Exception as e:
            logger.error(f"Erro inesperado em update_telemetry: {e}")

    @pyqtSlot(np.ndarray)
    def update_video_frame(self, frame):
        try:
            frame = cv2.flip(frame, -1)
            h, w, ch = frame.shape
            if h > 0 and w > 0:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)
                self.video_label.setPixmap(pixmap.scaled(
                    self.video_label.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                ))
        except Exception as e:
            logger.error(f"Erro ao atualizar frame de video: {e}")

    def closeEvent(self, event):
        logger.info("Fechando a aplicacao...")
        self.simulation_timer.stop()
        
        self.last_drive_payload = None 
        stop_payload = {"left": 0, "right": 0}
        self.command_signal.emit(config.TOPIC_COMMAND_DRIVE, json.dumps(stop_payload))
        QThread.msleep(100)

        logger.info("Sinalizando threads de fundo para encerrar...")
        self.stop_workers_signal.emit()

        self.mqtt_thread.quit()
        self.mqtt_thread.wait(1000)
        self.video_thread.quit()
        self.video_thread.wait(1000)
        
        logger.info("Threads encerradas. Saindo da aplicacao.")
        event.accept()

