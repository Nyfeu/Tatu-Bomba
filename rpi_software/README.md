# 🤖 Software da Raspberry Pi

Esta pasta contém todo o software que roda na **Raspberry Pi Zero 2W**, atuando como o 🧠 "cérebro" do robô. Ela faz a ponte entre o controle de baixo nível (ESP32) e o controle de alto nível (PC Dashboard), além de executar executar algoritmos e servidor de vídeo.

## 📦 Componentes

- **`config.py`**: Arquivo central de configuração para definir o endereço do broker MQTT e a porta serial.
- **`robot_client.py`**: Serviço principal. Lê pacotes binários do ESP32 via UART, retransmite telemetria para o broker MQTT e envia comandos do dashboard para o ESP32.
- **`video_server.py`**: Servidor web leve (Flask) que transmite o vídeo da câmera em formato MJPEG.
- **`requirements.txt`**: Lista de todas as dependências Python necessárias.

## ⚙️ Configuração do Ambiente (Primeira Vez)

### 🛠️ Instalar Dependências do Sistema

```bash
sudo apt update
sudo apt full-upgrade
sudo apt install -y python3-pip python3-venv libcamera-apps python3-picamera2 libcap-dev
```

### 🐍 Configurar o Ambiente Python

Navegue até esta pasta (`rpi_software/`) e crie um ambiente virtual:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

## 🏭 Para Produção (Inicialização Automática com systemd)

Para iniciar os serviços automaticamente com o robô, use os arquivos de serviço **systemd**.

1. **Edite os Arquivos de Serviço:**  
    Abra `robot-client.service` e `mjpeg-server.service` e verifique se o `User` e os caminhos em `WorkingDirectory` e `ExecStart` estão corretos para sua configuração.

2. **Instale e Ative os Serviços:**
    ```bash
    # Copie os serviços para a pasta do systemd
    sudo cp services/* /etc/systemd/system/

    # Recarregue, ative e inicie os serviços
    sudo systemctl daemon-reload
    sudo systemctl enable robot_client.service video_server.service
    sudo systemctl start robot_client.service video_server.service
    ```

3. **Verifique o Status e os Logs:**
    ```bash
    sudo systemctl status robot_client.service
    sudo journalctl -u robot_client.service -f
    ```

## 🔨 Testes

Além do código-fonte dos serviços que rodarão no **RPi**, há também códigos de teste em: `rpi_software\test` - são eles:
- **`robot_mock.py`**: Código responsável por mockar (simular) os dados gerados pela plataforma móvel, publicando nos tópicos MQTT, para testar o comportamento da telemetria no dashboard (do **pc_command_center**).
- **`teste_uart.py`**: Script responsável por testes de comunicação serial (UART) entre o **ESP32** e o **RPi**.