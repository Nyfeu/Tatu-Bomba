import io
import logging
import socketserver
from http import server
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

# --- Configuração da Página HTML Simples ---
# Isso cria uma página web básica para exibir o stream
PAGE = """
<html>
<head>
<title>Raspberry Pi - Câmera MJPEG</title>
</head>
<body>
<h1>Câmera MJPEG - Pi Zero 2W</h1>
<img src="stream.mjpg" width="640" height="480" />
</body>
</html>
"""

# --- Classe para Lidar com o Streaming ---
# Esta classe gerencia o envio dos frames da câmera para os clientes conectados
class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

# --- Classe para Lidar com as Requisições HTTP ---
# Define o que o servidor faz quando alguém acessa ele
class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

# --- Classe para o Servidor ---
class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# --- Execução Principal ---
picam2 = Picamera2()
# Configura a resolução do vídeo. Use resoluções menores para melhor performance no Pi Zero
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
output = StreamingOutput()
# Inicia o encoder para MJPEG e associa com a saída de streaming
picam2.start_recording(JpegEncoder(), FileOutput(output))

try:
    address = ('', 8000) # Deixa em branco para aceitar conexões de qualquer IP, na porta 8000
    server = StreamingServer(address, StreamingHandler)
    print("Servidor iniciado! Acesse http://<IP_DO_SEU_PI>:8000")
    server.serve_forever()
finally:
    picam2.stop_recording()
