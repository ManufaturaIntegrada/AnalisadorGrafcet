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

for /f "tokens=*" %%i in ('findstr "trycloudflare.com" tunnel.txt') do (
    echo %%i | findstr /R "https://.*trycloudflare.com" > temp.txt
)

for /f "tokens=*" %%i in (temp.txt) do (
    set URL=%%i
)

echo URL encontrada: %URL%
echo ================================
echo Atualizando scripts.js...
echo ================================

powershell -Command "(Get-Content js/scripts.js) -replace 'https://.*trycloudflare.com', '%URL%' | Set-Content js/scripts.js"

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