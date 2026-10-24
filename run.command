#!/bin/zsh
cd "${0:A:h}"
.venv/bin/python main.py
read "?Press Return to close this window"
