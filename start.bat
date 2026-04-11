@echo off
cd /d %~dp0

echo Verificando porta 5000...

netstat -ano | findstr :5000 > nul

if %errorlevel%==0 (
    echo Servidor ja esta rodando. Pulando inicializacao do Flask.
) else (
    echo Iniciando Flask...
    start cmd /k "cd backend && python app.py"
    timeout /t 4 > nul
)

echo ================================
echo Iniciando Cloudflare Tunnel...
echo ================================

start cmd /c "cloudflared tunnel --url http://localhost:5000 > tunnel.txt"

timeout /t 6 > nul

echo ================================
echo Extraindo URL...
echo ================================

set URL=

for /f "tokens=*" %%i in ('findstr /R "https://.*trycloudflare.com" tunnel.txt') do (
    set URL=%%i
)

REM limpa texto extra (pega só a URL)
for /f "tokens=2 delims= " %%a in ("%URL%") do set URL=%%a

echo URL encontrada: %URL%

echo ================================
echo Atualizando script.js...
echo ================================

powershell -Command "(Get-Content js/script.js) -replace 'URL_AQUI', '%URL%' | Set-Content js/script.js"

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