# ui_widgets.py
# Módulo com widgets modernizados para o dashboard HUD.
# - MAPA: Lógica de centralização reforçada.
# - BÚSSOLA: Ajustado o espaçamento vertical dos números.

import math
from PyQt6.QtWidgets import (QWidget, QGraphicsView, QGraphicsScene,
                             QGraphicsPathItem, QGraphicsPolygonItem, QLabel,
                             QGridLayout, QPushButton, QTextEdit)
from PyQt6.QtCore import pyqtSlot, Qt, QPointF, QRectF, QLineF, pyqtSignal
from PyQt6.QtGui import (QPen, QBrush, QColor, QPainterPath, QPolygonF,
                         QPainter, QFont, QLinearGradient, QTransform)

class TopLeftInfoWidget(QWidget):
    """Um painel moderno que combina indicadores de status e bateria."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 100)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.mqtt_status = "Desconectado"
        self.video_status = "Aguardando"
        self.battery_voltage = 0.0
        self.battery_percent = 0
        
        self.font_main = QFont('Segoe UI', 10, QFont.Weight.Bold)
        self.font_small = QFont('Segoe UI', 8)

    @pyqtSlot(str)
    def set_mqtt_status(self, status):
        self.mqtt_status = status
        self.update()

    @pyqtSlot(str)
    def set_video_status(self, status):
        self.video_status = status
        self.update()

    @pyqtSlot(float, int)
    def set_battery_value(self, voltage, percent):
        self.battery_voltage = voltage
        self.battery_percent = percent
        self.update()

    def _get_status_color(self, status):
        if "Conectado" in status: return QColor("#2ecc71")
        if "Conectando" in status: return QColor("#f39c12")
        return QColor("#e74c3c")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QBrush(QColor(27, 38, 59, 180)))
        painter.setPen(QPen(QColor(119, 141, 169, 150)))
        painter.drawRoundedRect(self.rect(), 10, 10)
        
        painter.setFont(self.font_main)
        
        mqtt_color = self._get_status_color(self.mqtt_status)
        painter.setPen(mqtt_color); painter.setBrush(mqtt_color)
        painter.drawEllipse(QPointF(20, 25), 5, 5)
        painter.setPen(QColor("#e0e1dd"))
        painter.drawText(QRectF(35, 15, 200, 20), Qt.AlignmentFlag.AlignVCenter, f"MQTT: {self.mqtt_status}")
        
        video_color = self._get_status_color(self.video_status)
        painter.setPen(video_color); painter.setBrush(video_color)
        painter.drawEllipse(QPointF(20, 50), 5, 5)
        painter.setPen(QColor("#e0e1dd"))
        painter.drawText(QRectF(35, 40, 200, 20), Qt.AlignmentFlag.AlignVCenter, f"Vídeo: {self.video_status}")

        battery_rect = QRectF(15, 70, self.width() - 30, 15)
        
        painter.setPen(QPen(QColor("#778da9"), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(battery_rect, 4, 4)
        
        bar_margin = 2
        bar_width = (battery_rect.width() - 2 * bar_margin) * (self.battery_percent / 100.0)
        bar_rect = QRectF(battery_rect.x() + bar_margin, battery_rect.y() + bar_margin,
                          bar_width, battery_rect.height() - 2 * bar_margin)
        
        gradient = QLinearGradient(battery_rect.topLeft(), battery_rect.topRight())
        gradient.setColorAt(0.0, QColor("#e74c3c"))
        gradient.setColorAt(0.4, QColor("#f39c12"))
        gradient.setColorAt(0.7, QColor("#2ecc71"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bar_rect, 2, 2)
        
        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(self.font_main)
        painter.drawText(battery_rect, Qt.AlignmentFlag.AlignCenter, f"{self.battery_percent}%")
        
        painter.setFont(self.font_small)
        painter.drawText(QRectF(self.width() - 80, 50, 70, 15), Qt.AlignmentFlag.AlignRight, f"{self.battery_voltage:.2f}V")


class ArtificialHorizonWidget(QWidget):
    # (Código inalterado)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.pitch = 0.0
        self.roll = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    @pyqtSlot(float, float)
    def set_angles(self, pitch, roll):
        self.pitch = pitch
        self.roll = roll
        self.update()

    # SUBSTITUA TODO O MÉTODO paintEvent POR ESTE:
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = self.width()
        height = self.height()
        center = QPointF(width / 2, height / 2)
        radius = min(width, height) / 2 - 5

        painter.save()
        
        # 1. Criar a área de recorte circular
        clip_path = QPainterPath()
        clip_path.addEllipse(center, radius, radius)
        painter.setClipPath(clip_path)

        # 2. Mover a origem para o centro, rotacionar para o ROLL e transladar para o PITCH
        painter.translate(center)
        painter.rotate(-self.roll)
        
        # O pitch é uma translação vertical, aplicada DEPOIS da rotação
        pitch_offset = self.pitch * 3
        painter.translate(0, pitch_offset)

        # 3. Desenhar o céu e a terra
        sky_gradient = QLinearGradient(0, -height, 0, 0)
        sky_gradient.setColorAt(0, QColor("#87CEEB"))
        sky_gradient.setColorAt(1, QColor("#4682B4"))
        ground_gradient = QLinearGradient(0, 0, 0, height)
        ground_gradient.setColorAt(0, QColor("#8B4513"))
        ground_gradient.setColorAt(1, QColor("#A0522D"))

        painter.setPen(Qt.PenStyle.NoPen)
        # O céu é um grande retângulo desenhado acima do horizonte (y=0)
        painter.setBrush(QBrush(sky_gradient))
        painter.drawRect(int(-width * 1.5), int(-height * 1.5), int(width * 3), int(height * 1.5))
        # A terra é um grande retângulo desenhado abaixo do horizonte (y=0)
        painter.setBrush(QBrush(ground_gradient))
        painter.drawRect(int(-width * 1.5), 0, int(width * 3), int(height * 1.5))

        # 4. Desenhar as linhas de pitch
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.setFont(QFont('Segoe UI', 8))
        for angle in range(-90, 91, 10):
            if angle == 0: continue
            y_pos = int(-angle * 3)  # A posição é relativa ao horizonte (0,0)
            line_width = int(radius / 4)
            painter.drawLine(int(-line_width), y_pos, int(line_width), y_pos)
            painter.drawText(QRectF(int(line_width + 5), y_pos - 8, 30, 16), Qt.AlignmentFlag.AlignLeft, str(abs(angle)))
            painter.drawText(QRectF(int(-line_width - 35), y_pos - 8, 30, 16), Qt.AlignmentFlag.AlignRight, str(abs(angle)))
        
        painter.drawLine(int(-radius * 1.5), 0, int(radius * 1.5), 0) # Linha do horizonte
        
        painter.restore()

        # --- Desenhar elementos estáticos (bezel, ponteiro de roll, avião) ---
        painter.setPen(QPen(QColor(119, 141, 169, 150), 2))
        painter.setBrush(QBrush(QColor(27, 38, 59, 180)))
        painter.drawEllipse(center, radius, radius)
        
        # Ponteiro de Roll (estático no topo)
        painter.save()
        painter.translate(center)
        roll_pointer = QPolygonF([QPointF(0, -radius+2), QPointF(-5, -radius + 12), QPointF(5, -radius + 12)])
        painter.setPen(QPen(QColor("#f1c40f"), 2))
        painter.setBrush(QBrush(QColor("#f1c40f")))
        painter.drawPolygon(roll_pointer)
        painter.restore()

        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.setFont(QFont('Segoe UI', 8, QFont.Weight.Bold))
        for angle in [-60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60]:
            painter.save()
            painter.translate(center)
            painter.rotate(angle)
            line_len = 10 if angle % 30 == 0 else 5
            painter.drawLine(0, int(-radius), 0, int(-radius + line_len))
            painter.restore()
        
        # Símbolo do avião (estático no centro)
        painter.setPen(QPen(QColor("#f1c40f"), 3))
        painter.drawLine(int(center.x() - 50), int(center.y()), int(center.x() - 10), int(center.y()))
        painter.drawLine(int(center.x() + 10), int(center.y()), int(center.x() + 50), int(center.y()))
        painter.drawEllipse(center, 3, 3)

class SpeedometerWidget(QWidget):
    # (Código inalterado)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.speed = 0.0
        self.max_speed = 100.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    @pyqtSlot(float)
    def set_speed(self, speed):
        self.speed = max(0, min(speed, self.max_speed))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = self.width(); height = self.height()
        center = QPointF(width / 2, height / 2)
        radius = min(width, height) / 2 - 10
        painter.setPen(QPen(QColor(119, 141, 169, 150), 2)); painter.setBrush(QBrush(QColor(27, 38, 59, 180)))
        painter.drawEllipse(center, radius, radius)
        arc_rect = QRectF(center.x() - radius + 8, center.y() - radius + 8, (radius - 8)*2, (radius - 8)*2)
        start_angle_deg = 210; total_span_deg = 240
        painter.setPen(QPen(QColor("#2ecc71"), 8))
        painter.drawArc(arc_rect, start_angle_deg * 16, int(-total_span_deg * 0.4) * 16)
        painter.setPen(QPen(QColor("#f39c12"), 8))
        painter.drawArc(arc_rect, int(start_angle_deg - total_span_deg * 0.4) * 16, int(-total_span_deg * 0.3) * 16)
        painter.setPen(QPen(QColor("#e74c3c"), 8))
        painter.drawArc(arc_rect, int(start_angle_deg - total_span_deg * 0.7) * 16, int(-total_span_deg * 0.3) * 16)
        painter.setPen(QPen(Qt.GlobalColor.white)); painter.setFont(QFont('Segoe UI', 10))
        end_angle_deg = -30
        for i in range(int(self.max_speed / 10) + 1):
            angle = start_angle_deg - (i * (start_angle_deg - end_angle_deg) / (self.max_speed / 10))
            rad = math.radians(angle)
            x1 = center.x() + (radius - 20) * math.cos(rad); y1 = center.y() - (radius - 20) * math.sin(rad)
            x2 = center.x() + (radius - 15) * math.cos(rad); y2 = center.y() - (radius - 15) * math.sin(rad)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            if i % 2 == 0:
                tx = center.x() + (radius - 35) * math.cos(rad); ty = center.y() - (radius - 35) * math.sin(rad)
                painter.drawText(QRectF(tx - 15, ty - 10, 30, 20), Qt.AlignmentFlag.AlignCenter, str(i * 10))
        needle_angle_deg = start_angle_deg - (self.speed / self.max_speed) * (start_angle_deg - end_angle_deg)
        painter.save(); painter.translate(center); painter.rotate(90 - needle_angle_deg)
        painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QColor("#e0e1dd"))
        needle = QPolygonF([QPointF(0, -radius + 15), QPointF(-4, 0), QPointF(4, 0)])
        painter.drawPolygon(needle)
        painter.restore()
        painter.setBrush(QColor("#778da9")); painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, 15, 15)
        painter.setFont(QFont('Segoe UI', 18, QFont.Weight.Bold)); painter.setPen(QPen(Qt.GlobalColor.white))
        painter.drawText(QRectF(center.x() - 50, center.y() + 20, 100, 30), Qt.AlignmentFlag.AlignCenter, f"{self.speed:.1f}")
        painter.setFont(QFont('Segoe UI', 10))
        painter.drawText(QRectF(center.x() - 50, center.y() + 45, 100, 20), Qt.AlignmentFlag.AlignCenter, "pixels/s")


class HorizontalCompassWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 80)
        self.heading = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    @pyqtSlot(float)
    def set_heading(self, heading):
        self.heading = heading
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        center_x = width / 2
        tape_height = height - 30 

        # Desenha o fundo
        background_rect = QRectF(0, 0, width, tape_height)
        painter.setBrush(QBrush(QColor(27, 38, 59, 180)))
        painter.setPen(QPen(QColor(119, 141, 169, 150)))
        painter.drawRoundedRect(background_rect, 10, 10)

        # --- INÍCIO DA CORREÇÃO ---
        # Salva o estado do painter e define uma área de corte (clipping)
        # Tudo o que for desenhado a seguir só aparecerá dentro desta área
        painter.save()
        painter.setClipRect(background_rect.adjusted(5, 5, -5, -5))

        painter.setFont(QFont('Segoe UI', 10))
        painter.setPen(QPen(Qt.GlobalColor.white))
        pixels_per_degree = 4

        for angle in range(int(self.heading) - 50, int(self.heading) + 51):
            angle_norm = angle % 360
            x_pos = center_x - (self.heading - angle) * pixels_per_degree

            if angle_norm % 10 == 0:
                painter.drawLine(int(x_pos), int(tape_height * 0.5), int(x_pos), int(tape_height * 0.8))
                if abs(x_pos - center_x) > 25:
                    if angle_norm % 90 == 0:
                        painter.setFont(QFont('Segoe UI', 11, QFont.Weight.Bold))
                        cardinals = {0: "N", 90: "E", 180: "S", 270: "W"}
                        painter.setPen(QColor("#e74c3c") if angle_norm == 0 else Qt.GlobalColor.white)
                        painter.drawText(QRectF(x_pos - 15, 5, 30, 20), Qt.AlignmentFlag.AlignCenter, cardinals[angle_norm])
                    else:
                        painter.setFont(QFont('Segoe UI', 9, QFont.Weight.Normal))
                        painter.setPen(Qt.GlobalColor.white)
                        painter.drawText(QRectF(x_pos - 15, 8, 30, 15), Qt.AlignmentFlag.AlignCenter, str(angle_norm))
            elif angle_norm % 5 == 0:
                painter.drawLine(int(x_pos), int(tape_height * 0.5), int(x_pos), int(tape_height * 0.65))
        
        # Restaura o estado do painter (remove a área de corte)
        painter.restore()
        # --- FIM DA CORREÇÃO ---

        # Desenha o ponteiro central (agora por cima da área de corte)
        painter.setPen(QPen(QColor("#f1c40f"), 2)) # Linha mais fina
        painter.drawLine(QPointF(center_x, 5), QPointF(center_x, tape_height - 5))
        
        # Desenha a caixa com o valor numérico
        text_rect = QRectF(center_x - 35, tape_height + 2, 70, 25)
        painter.setBrush(QBrush(QColor(13, 27, 42, 200)))
        painter.setPen(QPen(QColor(119, 141, 169, 150)))
        painter.drawRoundedRect(text_rect, 5, 5)

        painter.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, f"{self.heading % 360:.0f}°")

class MapWidget(QGraphicsView):
    reset_map_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(13, 27, 42, 200)))
        self.setStyleSheet("border: none;")

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Itens da cena (caminho e robô)
        self.path = QPainterPath()
        self.path_item = QGraphicsPathItem()
        self.path_item.setPen(QPen(QColor("#1abc9c"), 2, Qt.PenStyle.DashLine))
        self.scene.addItem(self.path_item)

        robot_shape = QPolygonF([
            QPointF(12, 0), QPointF(-8, -8),
            QPointF(-3, 0), QPointF(-8, 8)
        ])
        self.robot_item = QGraphicsPolygonItem(robot_shape)
        self.robot_item.setBrush(QBrush(QColor("#e0e1dd")))
        self.robot_item.setPen(QPen(Qt.PenStyle.NoPen))
        self.scene.addItem(self.robot_item)

        # Apenas prepara os dados, não mexe na câmara ainda
        self._reset_scene_data()

    def showEvent(self, event):
        """
        Este método é chamado quando o widget está prestes a ser exibido.
        É o local perfeito para configurar a vista inicial da câmara,
        pois aqui o widget já tem o seu tamanho final.
        """
        super().showEvent(event)
        # Configura a vista da câmara pela primeira vez
        self._reset_view()

    def _reset_scene_data(self):
        """Função interna para resetar apenas os dados da cena."""
        self.path = QPainterPath(QPointF(0, 0))
        self.path_item.setPath(self.path)
        self.robot_item.setPos(0, 0)
        self.robot_item.setRotation(0)

    def _reset_view(self):
        """Função interna para resetar a transformação e centralização da câmara."""
        self.resetTransform()
        self.rotate(-90)
        self.centerOn(self.robot_item)

    @pyqtSlot()
    def reset_map(self):
        """
        Slot público chamado pelo botão RESET.
        Reseta tanto os dados da cena como a vista da câmara.
        """
        self._reset_scene_data()
        self._reset_view()

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        grid_size = 50
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        lines = []
        x = left
        while x < rect.right():
            lines.append(QLineF(x, rect.top(), x, rect.bottom())); x += grid_size
        y = top
        while y < rect.bottom():
            lines.append(QLineF(rect.left(), y, rect.right(), y)); y += grid_size
        painter.setPen(QPen(QColor(27, 38, 59, 220), 1))
        painter.drawLines(lines)

    @pyqtSlot(float, float)
    def add_path_point(self, x, y):
        self.path.lineTo(x, -y)
        self.path_item.setPath(self.path)

    @pyqtSlot(float, float, float)
    def update_robot_pose(self, x, y, angle_deg):
        # 1. Atualiza a posição e rotação do item do robô na cena
        self.robot_item.setPos(x, -y)
        self.robot_item.setRotation(-angle_deg)
        
        # --- INÍCIO DA LÓGICA DE CENTRALIZAÇÃO ---
        # 2. Reseta completamente qualquer transformação anterior da câmera (zoom, pan, rotação)
        self.resetTransform()

        # 1. Centraliza primeiro no robô
        self.centerOn(self.robot_item)

        # 2. Depois aplica a rotação da câmera
        self.rotate(angle_deg - 90)

        # 3. E por último, força centralização de novo (corrige o deslocamento pós-rotação)
        self.centerOn(self.robot_item)
        # --- FIM DA LÓGICA DE CENTRALIZAÇÃO ---

class MapContainerWidget(QWidget):
    """Container para o mapa e o seu botão de reset."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.map_widget = MapWidget()
        
        self.reset_button = QPushButton("RESET")
        self.reset_button.setFixedSize(60, 25)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(27, 38, 59, 220);
                color: white;
                border: 1px solid rgba(119, 141, 169, 200);
                border-radius: 5px;
                font-family: 'Segoe UI';
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(47, 58, 79, 220);
            }
            QPushButton:pressed {
                background-color: rgba(7, 18, 39, 220);
            }
        """)
        
        self.reset_button.clicked.connect(self.map_widget.reset_map_signal.emit)

        layout = QGridLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.map_widget, 0, 0)
        layout.addWidget(self.reset_button, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)


class KeyIndicatorWidget(QWidget):
    # (Código inalterado)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QGridLayout(self)
        self.key_labels = {'W': QLabel("W"), 'A': QLabel("A"), 'S': QLabel("S"), 'D': QLabel("D")}
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(27, 38, 59, 180); color: #778da9;
                border: 2px solid #415a77; border-radius: 5px;
                font-size: 20px; font-weight: bold;
                min-width: 50px; min-height: 50px;
            }
            QLabel[active="true"] {
                background-color: #778da9; color: #ffffff;
                border: 2px solid #e0e1dd;
            }
        """)
        for key, label in self.key_labels.items():
            label.setAlignment(Qt.AlignmentFlag.AlignCenter); label.setProperty("active", False)
        layout.addWidget(self.key_labels['W'], 0, 1)
        layout.addWidget(self.key_labels['A'], 1, 0)
        layout.addWidget(self.key_labels['S'], 1, 1)
        layout.addWidget(self.key_labels['D'], 1, 2)

    def update_keys(self, keys_pressed):
        for key, label in self.key_labels.items():
            is_active = key in keys_pressed
            if label.property("active") != is_active:
                label.setProperty("active", is_active)
                label.style().polish(label)

class RawTelemetryWidget(QWidget):
    """Um widget para exibir o payload MQTT bruto."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 200)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QGridLayout(self)
        layout.setContentsMargins(10, 5, 10, 10)
        
        title_label = QLabel("MQTT Telemetry Data")
        title_label.setFont(QFont('Segoe UI', 9, QFont.Weight.Bold))
        title_label.setStyleSheet("color: '#e0e1dd';")
        
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont('Consolas', 8))
        self.text_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(13, 27, 42, 220);
                color: '#1abc9c';
                border: 1px solid rgba(119, 141, 169, 150);
                border-radius: 5px;
            }
        """)
        
        layout.addWidget(title_label, 0, 0)
        layout.addWidget(self.text_display, 1, 0)

    @pyqtSlot(str)
    def update_telemetry(self, payload_str):
        self.text_display.setText(payload_str)