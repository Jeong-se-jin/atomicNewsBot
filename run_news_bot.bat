@echo off
cd /d "c:\Users\user\Desktop\projects\newsbot"

SET PYTHONIOENCODING=utf-8

echo ================================ >> run_log.txt
echo Start: %date% %time% >> run_log.txt
echo Directory: %CD% >> run_log.txt
where python >> run_log.txt 2>&1
echo ================================ >> run_log.txt

echo [1/1] Running main.py... >> run_log.txt
python main.py >> run_log.txt 2>&1
echo main.py finished (Exit Code: %ERRORLEVEL%) >> run_log.txt

echo. >> run_log.txt
echo Completed! >> run_log.txt
echo End: %date% %time% >> run_log.txt
echo ================================ >> run_log.txt
echo. >> run_log.txt
