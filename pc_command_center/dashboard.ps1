# Script PowerShell para configurar o ambiente Python e executar o dashboard.

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
Write-StyledHost "  Iniciador do Dashboard (Tatu-Bomba)  " "Cyan"
Write-StyledHost "=======================================" "Cyan"
Write-Host ""

# --- 1. Gestao do Ambiente Virtual (venv) ---
$VenvDir = ".\venv"
if (-not (Test-Path $VenvDir)) {
    Write-StyledHost "Ambiente virtual Python ('venv') nao encontrado." -Color "Yellow"
    Write-StyledHost "Criando ambiente virtual..." -Color "Yellow" -Indent 2
    try {
        python -m venv venv
        Write-StyledHost "[OK] Ambiente virtual criado com sucesso." -Color "Green" -Indent 2
    } catch {
        Write-StyledHost "[ERRO] Falha ao criar o ambiente virtual. Verifique a sua instalacao do Python." -Color "Red" -Indent 2
        exit 1
    }
} else {
    Write-StyledHost "[OK] Ambiente virtual encontrado." -Color "Green" -Indent 2
}
Write-Host ""

# Ativa o ambiente virtual
Write-StyledHost "Ativando ambiente virtual..." -Color "Yellow"
try {
    . ($VenvDir + "\Scripts\Activate.ps1")
    Write-StyledHost "[OK] Ambiente virtual ativado." -Color "Green" -Indent 2
} catch {
    Write-StyledHost "[ERRO] Nao foi possivel ativar o ambiente virtual." -Color "Red" -Indent 2
    exit 1
}
Write-Host ""

# --- 2. Instalacao de Dependencias ---
Write-StyledHost "Instalando/verificando dependencias do Python a partir de 'requirements.txt'..." -Color "Yellow"
pip install -r requirements.txt | Out-Null
Write-StyledHost "[OK] Dependencias instaladas." -Color "Green" -Indent 2
Write-Host ""

# --- 3. Execucao da Aplicacao ---
Write-StyledHost "Iniciando o dashboard..." -Color "Cyan"
Write-Host "Pressione Ctrl+C no terminal ou feche a janela para encerrar."
Write-Host ""

try {
    # Executa o dashboard
    python .\dashboard\main.py
} finally {
    # Desativa o ambiente virtual ao terminar
    Write-Host ""
    Write-StyledHost "Dashboard encerrado. Desativando ambiente virtual..." -Color "Yellow"
    deactivate
    Write-StyledHost "[OK] Ambiente encerrado." -Color "Green" -Indent 2
}
