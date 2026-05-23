from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import httpx
from dotenv import load_dotenv
from typing import Optional
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

# 讀取保險箱裡的密碼
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
COIN_API_KEY = os.getenv("COIN_API_KEY", "JXm9LpRc3wKvDq8HtFyN2bZx4CgA7sE5M=")
COIN_API_URL = os.getenv("COIN_API_URL", "https://telegram-bot.luyiqi-lili.workers.dev/api/coin")
BOT_WALLET_ID = os.getenv("BOT_WALLET_ID") # 記得在 .env 補上機器人的錢包 ID

app = FastAPI()

# 在 app = FastAPI() 下方加入一個啟動 Bot 的函數
async def run_bot():
    token = os.getenv("TELEGRAM_TOKEN")
    # 從 main.py 搬過來的邏輯
    app_bot = ApplicationBuilder().token(token).build()
    
    # 註冊指令 (記得補上妳原本 main.py 裡的 poker_cmd 等函數)
    # app_bot.add_handler(...)
    
    await app_bot.initialize()
    await app_bot.start()
    await app_bot.updater.start_polling()

# 在 if __name__ == "__main__": 的啟動邏輯中加入
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_bot())

# 允許跨域請求
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# 掛載靜態網頁資料夾 (之後超華麗的 index.html 會放這裡)
DIRECTORY = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(DIRECTORY):
    os.makedirs(DIRECTORY)
app.mount("/static", StaticFiles(directory=DIRECTORY), name="static")

# ==========================================
# 💰 金流系統 (Coin API 串接)
# ==========================================

async def get_coin_balance(user_id: str):
    """查詢玩家餘額 (非同步版本)"""
    url = f"{COIN_API_URL}/get?key={user_id}"
    headers = {"X-API-Key": COIN_API_KEY}
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, dict):
                    return int(data.get("balance", data.get("coin", data.get("data", 0))))
                return int(data)
    except Exception as e:
        print(f"❌ 查詢餘額失敗: {e}")
    return 0

async def transfer_coin(from_uid: str, to_uid: str, amount: int):
    """處理玩家與莊家之間的資金轉帳 (非同步版本)"""
    if amount <= 0: return True
    if not from_uid or not to_uid:
        print("❌ [轉帳失敗] 缺少玩家 ID！")
        return False
        
    url = f"{COIN_API_URL}/transfer"
    headers = {
        "Content-Type": "application/json", 
        "X-API-Key": COIN_API_KEY
    }
    data = {
        "from": str(from_uid), 
        "to": str(to_uid), 
        "amount": int(amount)
    }
    
    print(f"💸 [準備轉帳] 從 {from_uid} 轉 {amount} Coin 到 {to_uid} ...")
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=headers, json=data)
            print(f"🔍 [API 回應] Status: {res.status_code} | Body: {res.text}")
            
            if res.status_code == 200:
                try:
                    res_json = res.json()
                    # 確保 API 真的回傳成功狀態
                    if res_json.get("code") in [200, "200"] or res_json.get("success") or res_json.get("ok"):
                        return True
                except:
                    pass # 如果回傳的不是 JSON，只要 status 200 也當作成功
                return True
    except Exception as e:
        print(f"❌ [轉帳發生錯誤] {e}")
    return False

# ==========================================
# 🎮 遊戲與網頁路由
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def serve_game():
    """回傳德州撲克遊戲主畫面"""
    file_path = os.path.join(DIRECTORY, "index.html")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>♠️ ♥️ 薇拉還在準備牌桌喔！(index.html 尚未建立) ♣️ ♦️</h1>"

# 德州撲克的房間邏輯與 WebSocket/API 將會接在這裡...
# (之後我們會建立 /api/room/{room_id} 等路由來處理下注和發牌)

if __name__ == "__main__":
    print("🚀 薇拉的德州撲克伺服器啟動中...")
    # 自動偵測 Render 的 Port，偵測不到就預設用 8080
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("server:app", host="0.0.0.0", port=port)