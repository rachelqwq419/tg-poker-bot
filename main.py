import os
import logging
import urllib.parse
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# 設定 Logging，讓薇拉幫妳盯著系統運作日誌！👀
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 讀取保險箱裡的密碼
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GAME_SHORT_NAME = os.getenv("GAME_SHORT_NAME", "poker")

# ⚠️ 這裡先寫一個暫時的 WebApp 網址，等我們上傳 Render 拿到真實網址後再來換掉！
WEBAPP_URL = "WEBAPP_URL" 

async def poker_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /poker 指令，發送遊戲卡片"""
    try:
        chat_id = update.effective_chat.id
        # 如果大家在群組的討論串裡玩，確保機器人會回覆在同一個討論串
        thread_id = update.message.message_thread_id if update.message else None
        
        await context.bot.send_game(
            chat_id=chat_id, 
            game_short_name=GAME_SHORT_NAME, 
            message_thread_id=thread_id
        )
    except Exception as e:
        logger.error(f"發送遊戲失敗: {str(e)}")

async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理玩家點擊 Play 按鈕，生成專屬網址"""
    query = update.callback_query
    try:
        # 抓取玩家的 ID 和名字
        chat_id = str(query.message.chat.id)
        user_id = str(query.from_user.id)
        raw_name = query.from_user.first_name
        
        # 把名字轉換成網址安全格式（避免有特殊符號壞掉）
        safe_name = urllib.parse.quote(raw_name)
        
        # 組合我們專屬的遊戲網址，把玩家資料偷渡給前端！
        room_url = f"{WEBAPP_URL}?room={chat_id}&uid={user_id}&uname={safe_name}"
        
        # 彈出 WebApp 視窗
        await query.answer(url=room_url)
    except Exception as e:
        logger.error(f"處理點擊回調失敗: {str(e)}")

if __name__ == "__main__":
    print("✨ 薇拉正在啟動 Telegram 機器人接待員... ✨")
    # 建立機器人應用程式
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # 註冊指令跟按鈕的監聽器
    app.add_handler(CommandHandler("poker", poker_cmd))
    app.add_handler(CommandHandler("start", poker_cmd))
    app.add_handler(CallbackQueryHandler(game_callback))
    
    # 開始乖乖等玩家傳訊息
    app.run_polling()