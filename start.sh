#!/bin/bash
# 讓 Render 同時執行機器人跟網頁伺服器
python main.py &
python server.py