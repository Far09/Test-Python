Param(
    [string]$PythonBin = "python"
)

$ErrorActionPreference = "Stop"

Write-Host "==> Instalando/atualizando PyInstaller"
& $PythonBin -m pip install --upgrade pip pyinstaller

Write-Host "==> Limpando builds anteriores"
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }

$nome = "portal-chamados"

Write-Host "==> Gerando executável"
& $PythonBin -m PyInstaller --onefile --name $nome portal_chamados.py

Write-Host "Executável gerado em: dist/$nome.exe"
