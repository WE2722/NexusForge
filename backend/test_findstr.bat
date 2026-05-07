@echo off
echo {"devDependencies": {"vite": "1.0"}} > test.json
findstr /R /C:"\"dev\"[ \t]*:" test.json >nul
echo ErrorLevel for devDependencies: %errorlevel%

echo {"scripts": {"dev": "vite"}} > test.json
findstr /R /C:"\"dev\"[ \t]*:" test.json >nul
echo ErrorLevel for dev: %errorlevel%

echo {"scripts": {"dev" : "vite"}} > test.json
findstr /R /C:"\"dev\"[ \t]*:" test.json >nul
echo ErrorLevel for dev with space: %errorlevel%
