@echo off
cd /d "%~dp0"
echo.
echo  Enviando atualizacoes para o GitHub...
echo.
git add .
git commit -m "atualizado"
git pull --rebase origin main
git push
echo.
echo  Pronto! Dados sincronizados.
pause
