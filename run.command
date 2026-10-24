#!/bin/zsh
cd "${0:A:h}"
.venv/bin/python main.py
read "?按回车关闭窗口"
