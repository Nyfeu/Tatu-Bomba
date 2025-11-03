# Centro de Comando do PC (Dashboard e Broker)

Este diretório contém o software necessário para operar o ambiente do operador no PC, composto por dois componentes principais:

- **Broker MQTT (Mosquitto) 📨:** Servidor central de mensagens, executado de forma isolada em um container Docker para maior estabilidade.
- **Dashboard (PyQt) 🖥️:** Aplicação gráfica local para controle e visualização de telemetria.

## Arquitetura e Automação ⚙️

Cada componente é gerenciado por seu próprio script PowerShell, promovendo o fluxo de trabalho:

- **Infraestrutura:** O broker é controlado pelo script `mosquitto.ps1`.
- **Aplicação:** O dashboard é iniciado pelo script `dashboard.ps1`.

## Pré-requisitos 📋

Antes de começar, certifique-se de ter os seguintes softwares instalados e funcionando no seu PC:

- **Docker Desktop:** Necessário para executar o container Mosquitto.
- **Python 3:** Requisito para rodar o dashboard e suas dependências.
- **Dependências Python:** As bibliotecas necessárias (PyQt6, OpenCV, etc.) são instaladas automaticamente pelo `dashboard.ps1` em um ambiente virtual (venv).

## Como Executar 🚀

### 1. Iniciar a Infraestrutura (Broker)

Primeiramente, execute:

```powershell
.\mosquitto.ps1 start
```

O script irá:

- Verificar se o Docker está disponível.
- Iniciar o container Mosquitto.
- Confirmar que o broker está online.

### 2. Iniciar a Aplicação (Dashboard)

Na sequência, execute:

```powershell
.\dashboard.ps1
```

O script irá:

- Criar um ambiente virtual (na primeira execução).
- Instalar automaticamente as dependências.
- Iniciar a interface gráfica do dashboard.
- Conectar-se ao broker (MQTT) e ao stream de vídeo (MJPEG).

## Como Encerrar 🛑

- Feche a janela do dashboard ou pressione `Ctrl+C` no terminal.
- Em seguida, pare o broker de forma com:

```powershell
.\mosquitto.ps1 stop
```
