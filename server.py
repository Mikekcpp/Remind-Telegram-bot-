from bot import dp, on_startup
from aiogram import executor
from flask import Flask
import threading
import asyncio

app = Flask(__name__)
index = open("static/index.html", encoding="utf-8").read()


def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, loop=loop)


# Запуск бота в отдельном потоке
bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()


@app.route("/")
def root():
    print("index!")
    return index


if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)  # Отключаем reloader
