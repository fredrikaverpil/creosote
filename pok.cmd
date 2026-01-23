@echo off
setlocal EnableDelayedExpansion

:: Resolve shim directory to find .pocket
set "SHIM_DIR=%~dp0"
set "POCKET_DIR=%SHIM_DIR%.pocket"
set "TASK_SCOPE=."

go run -C "%POCKET_DIR%" . %*
