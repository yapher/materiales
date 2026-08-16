@echo off
echo =========================================
echo   IA Mezclas Industriales - Test Suite
echo =========================================
echo.

REM Instalar dependencias de testing si no están
pip install pytest pytest-flask pytest-cov -q

echo Ejecutando tests...
echo.

REM Ejecutar con verbose y resumen corto
pytest tests/ -v --tb=short

echo.
echo =========================================
echo   Para ejecutar con cobertura:
echo   pytest tests/ -v --cov=. --cov-report=term-missing
echo =========================================