@echo off
echo {"scripts": {"start": "echo STARTED"}} > test2.json
start cmd /k "npm --prefix . run dev || npm --prefix . start"
