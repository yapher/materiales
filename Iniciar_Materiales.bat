@echo off
title Materiales V1 - IA Mezclas Industriales
cd /d "%~dp0"

echo ============================================
echo   Materiales V1 - IA Mezclas Industriales
echo ============================================
echo.
echo Si es la primera vez, esto puede tardar unos
echo minutos (instala dependencias de Python).
echo NO cierres esta ventana.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_and_run.ps1"

echo.
echo ============================================
echo La app se detuvo o la ventana de PowerShell se cerro.
echo Podes cerrar esta ventana.
echo ============================================
pause
