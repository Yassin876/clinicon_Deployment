@echo off
echo Installing RAG dependencies...
cd /d D:\Projects\SPHG
pip install -r requirements.txt
echo.
echo Done! Now run: python rag_server.py
pause
