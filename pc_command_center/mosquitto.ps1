# Script PowerShell para iniciar e parar o broker Mosquitto via Docker.

[CmdletBinding()]
param (
    # Define a ação a ser executada: START ou STOP.
    # É um parâmetro posicional obrigatório.
    [Parameter(Mandatory=$true, Position=0, HelpMessage="Especifique a acao: START ou STOP.")]
    [ValidateSet('START', 'STOP', IgnoreCase = $true)]
    [string]$Action
)

# Garante que o script corre a partir da sua propria pasta
try {
    Set-Location $PSScriptRoot -ErrorAction Stop
} catch {
    Write-Error "Nao foi possivel determinar o diretorio do script. Execute a partir da pasta correta."
    exit 1
}

# --- Funcao Auxiliar para Output com Estilo ---
function Write-StyledHost {
    param (
        [string]$Message,
        [string]$Color = "White",
        [int]$Indent = 0
    )
    $indentation = " " * $Indent
    Write-Host "$indentation$Message" -ForegroundColor $Color
}

# --- Banner da Aplicacao ---
Write-StyledHost "=======================================" "Cyan"
Write-StyledHost "  Gestor de Broker MQTT (Tatu-Bomba) " "Cyan"
Write-StyledHost "=======================================" "Cyan"
Write-Host ""

# --- Verificacao do Docker ---
Write-StyledHost "Verificando o status do Docker Engine..." -Color "Yellow"
try {
    docker info | Out-Null
    Write-StyledHost "[OK] Docker esta a correr." -Color "Green" -Indent 2
} catch {
    Write-StyledHost "[ERRO] O Docker Engine nao esta a correr. Abra o Docker Desktop e tente novamente." -Color "Red" -Indent 2
    exit 1
}
Write-Host ""

# --- Logica Principal baseada na Acao ---
switch ($Action.ToUpper()) {
    'START' {
        Write-StyledHost "Iniciando o broker Mosquitto em segundo plano..." -Color "Yellow"
        docker-compose up -d
        Write-StyledHost "[OK] Comando 'docker-compose up' enviado." -Color "Green" -Indent 2
        Write-Host ""

        Write-StyledHost "Aguardando o broker Mosquitto ficar online..." -Color "Yellow"
        $startTime = Get-Date
        $timeoutSeconds = 30
        $spinner = @('|', '/', '-', '\')
        $spinnerIndex = 0

        while (((Get-Date) - $startTime).TotalSeconds -lt $timeoutSeconds) {
            if ((Test-NetConnection -ComputerName "localhost" -Port 1883 -WarningAction SilentlyContinue).TcpTestSucceeded) {
                Write-Host -NoNewline "`r" # Limpa a linha do spinner
                Write-StyledHost "[OK] Mosquitto esta online e a aceitar conexoes!" -Color "Green" -Indent 2
                Write-Host ""
                Write-StyledHost "Pode agora iniciar o dashboard noutro terminal."
                exit 0
            }
            # Animação de Spinner
            Write-Host -NoNewline "`r  Aguardando... [$($spinner[$spinnerIndex++ % $spinner.Length])]"
            Start-Sleep -Milliseconds 200
        }

        # Se sair do loop, deu timeout
        Write-Host "`r" # Limpa a linha do spinner
        Write-StyledHost "[ERRO] Timeout: Mosquitto nao ficou disponivel na porta 1883." -Color "Red" -Indent 2
        docker-compose down # Tenta limpar em caso de falha
        exit 1
    }

    'STOP' {
        Write-StyledHost "Parando e removendo o container do Mosquitto..." -Color "Yellow"
        docker-compose down
        Write-StyledHost "[OK] Broker encerrado com sucesso." -Color "Green" -Indent 2
    }
}

