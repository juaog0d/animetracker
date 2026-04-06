@echo off
cd /d "%~dp0"
echo.
echo  Baixando atualizacoes do GitHub...
echo.
git pull origin main
echo.
echo  Pronto! Abrindo o site...
start index.html
