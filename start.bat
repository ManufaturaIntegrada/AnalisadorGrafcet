@echo off
cd /d %~dp0

echo Verificando porta 5000...

netstat -ano | findstr :5000 > nul

if %errorlevel%==0 (
    echo Servidor ja esta rodando. Pulando inicializacao do Flask.
) else (
    echo Iniciando Flask...
    start cmd /k "cd backend && python app.py"
    timeout /t 5 > nul
)

echo ================================
echo Iniciando Cloudflare Tunnel...
echo ================================

start cmd /c "cloudflared tunnel --url http://localhost:5000 > tunnel.txt 2>&1"

timeout /t 10 > nul

echo ================================
echo Aguardando URL do tunnel...
echo ================================

set URL=

:loop
timeout /t 2 > nul

for /f %%i in ('powershell -Command "(Get-Content tunnel.txt | Select-String -Pattern 'https://.*trycloudflare.com').Matches.Value"') do (
    set URL=%%i
)

if "%URL%"=="" (
    echo Aguardando URL...
    goto loop
)

echo URL encontrada: %URL%
echo ================================
echo Atualizando scripts.js...
echo ================================

powershell -Command "(Get-Content js/scripts.js) -replace 'const API_URL = \".*\"', 'const API_URL = \"%URL%\"' | Set-Content js/scripts.js"

echo ================================
echo Enviando para GitHub...
echo ================================

git add .
git commit -m "Atualizando URL do tunnel"
git push

echo ================================
echo Finalizado!
echo ================================
pause