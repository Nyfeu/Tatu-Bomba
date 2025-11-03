import serial
import struct
import time
import threading

# Tenta abrir a porta serial. No RPi Zero 2W, geralmente é '/dev/ttyS0'.
SERIAL_PORT = "/dev/ttyS0"
BAUD_RATE = 115200

ser = None
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Porta serial {SERIAL_PORT} aberta com sucesso.")
except serial.SerialException as e:
    print(f"ERRO: Não foi possível abrir a porta serial {SERIAL_PORT}: {e}")
    print("Verifique as conexões, permissões (sudo) e configurações do RPi (raspi-config).")
    exit()

# --- FORMATO DA STRUCT SEM O CHECKSUM ---
# Formato original: '<B q f f h i i H B'
# O último 'B' (checksum) foi removido.
TELEMETRY_FORMAT = '<B q f f h i i H'
TELEMETRY_SIZE = struct.calcsize(TELEMETRY_FORMAT)

# --- Função para Receber e Decodificar Telemetria (em uma thread separada) ---

def read_telemetry():
    """Lê e decodifica os pacotes binários de telemetria do ESP32."""
    print("Thread de telemetria iniciada. Aguardando dados...")
    while True:
        if not ser or not ser.is_open:
            break

        try:
            start_byte = ser.read(1)
            if start_byte == b'\xaa':
                # Lê o tamanho do pacote SEM o checksum.
                # O último byte enviado pelo ESP32 (o checksum não calculado) será ignorado.
                packet_data = ser.read(TELEMETRY_SIZE - 1)
                
                if len(packet_data) == TELEMETRY_SIZE - 1:
                    full_packet = start_byte + packet_data
                    
                    try:
                        # Desempacota os dados sem esperar pelo checksum
                        unpacked_data = struct.unpack(TELEMETRY_FORMAT, full_packet)
                        start, ts, pitch, roll, gz, enc_l, enc_r, batt = unpacked_data
                        
                        # --- LÓGICA DE CHECKSUM REMOVIDA ---
                        print(f"\r\033[KTelemetria: Pitch={pitch:6.2f}, Roll={roll:6.2f}, EncL={enc_l:6d}, EncR={enc_r:6d}, Batt={batt/1000.0:.2f}V | Digite o comando: ", end="")

                    except struct.error:
                        print("\r\033[KErro ao desempacotar os dados.", end="")
        
        except serial.SerialException:
            print("\nErro na porta serial. Encerrando thread de telemetria.")
            break

# --- O resto do script (print_instructions, if __name__ == "__main__":, etc.) continua exatamente o mesmo ---
# (O código para enviar comandos não precisa de alteração)

def print_instructions():
    """Imprime as instruções de uso do terminal interativo."""
    print("\n--- Terminal de Controle do Robô ---")
    print("Comandos (use as teclas W, A, S, D):")
    print("  w [vel]   - Mover para frente (ex: w 80)")
    print("  s [vel]   - Mover para trás (ex: s 50)")
    print("  a [vel]   - Virar à esquerda (ex: a 40)")
    print("  d [vel]   - Virar à direita (ex: d 40)")
    print("  stop      - Parar os motores")
    print("  exit      - Sair do programa")
    print("------------------------------------")


if __name__ == "__main__":
    telemetry_thread = threading.Thread(target=read_telemetry, daemon=True)
    telemetry_thread.start()
    print_instructions()
    try:
        while True:
            command_input = input("").strip().lower()
            parts = command_input.split()
            if not parts:
                continue
            cmd = parts[0]
            if cmd == "exit":
                print("Saindo...")
                break
            if cmd == "stop":
                command = "DRIVE:0,0\n"
                ser.write(command.encode('ascii'))
                continue
            try:
                speed = int(parts[1]) if len(parts) > 1 else 70
                speed = max(0, min(100, speed))
            except (ValueError, IndexError):
                speed = 70
            command = ""
            if cmd == 'w':
                command = f"DRIVE:{speed},{speed}\n"
            elif cmd == 's':
                command = f"DRIVE:{-speed},{-speed}\n"
            elif cmd == 'a':
                command = f"DRIVE:{-speed},{speed}\n"
            elif cmd == 'd':
                command = f"DRIVE:{speed},{-speed}\n"
            else:
                print("\nComando inválido! Tente novamente.")
                continue
            ser.write(command.encode('ascii'))
    except KeyboardInterrupt:
        print("\nEncerrando por interrupção do teclado...")
    finally:
        if ser and ser.is_open:
            print("Enviando comando de parada final.")
            ser.write(b"DRIVE:0,0\n")
            ser.close()
            print("Conexão serial fechada.")