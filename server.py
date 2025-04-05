from bot import dp, executor  # Импортируем необходимые компоненты из bot.py
from flask import Flask
import threading
import asyncio


app = Flask(__name__)
index = open("static/index.html", encoding="utf-8").read()


# Функция для запуска бота
def run_bot():
    loop = asyncio.new_event_loop()  # Создаем новый цикл событий
    asyncio.set_event_loop(loop)  # Устанавливаем его как текущий для потока
    executor.start_polling(dp, skip_updates=True)  # Запускаем бота



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
