from bot import dp, executor  # Импортируем необходимые компоненты из bot.py
from flask import Flask
import threading
import asyncio

app = Flask(__name__)
index = open("static/index.html", encoding="utf-8").read()


# Функция для запуска бота
def run_bot():
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
    

# Запуск бота в отдельном потоке
bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True  # Поток завершится, если основной поток завершится
bot_thread.start()


# Process index page
@app.route("/")
def root():
    print("index!")
    return index


if __name__ == "__main__":
    app.run(debug=False)  # Отключаем debug, чтобы избежать перезапуска
