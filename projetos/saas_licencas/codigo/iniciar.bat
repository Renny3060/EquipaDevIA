@echo off
title Servidor de Licencas SaaS
echo A iniciar o servidor backend...
cd /d "C:\Users\migue\Desktop\EquipaDevIA\projetos\saas_licencas\codigo"
uvicorn main:app --reload
pause