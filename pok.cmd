@echo off
setlocal EnableDelayedExpansion

set "POK_DIR=.pocket"
set "POK_CONTEXT=."

go run -C "%POK_DIR%" . %*
