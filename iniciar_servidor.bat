@echo off
title Servidor SaaS Presupuestos
echo =======================================================
echo    Iniciando Servidor de Presupuestos SaaS (Port 8080)
echo =======================================================
cd /d "c:\Users\Usuario\Desktop\AntiGravity Proyectos\Generador_Presupuestos_SaaS"
python -m uvicorn main:app --port 8080
pause
