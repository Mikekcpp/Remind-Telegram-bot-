from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters import Command
from datetime import datetime, timedelta
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode
from os import environ
import logging
import asyncio

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s [LINE:%(lineno)d] # %(levelname)-8s [%(asctime)s]  %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
)

# Конфигурация
TELEGRAM_TOKEN = environ["TELEGRAM_TOKEN"]
ADMIN_IDS = [1294375064, 528911118]
GROUP_CHAT_ID = "-1001234567890"  

# Инициализация бота
bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Состояния для FSM
class ScheduleStates(StatesGroup):
    waiting_for_day = State()
    waiting_for_time = State()
    waiting_for_event_name = State()
    waiting_for_event_date = State()
    waiting_for_event_reminder = State()


# База данных (временная, для примера)
schedule = {
    "default_day": 1,  # 0-понедельник, 1-вторник и т.д.
    "default_time": "15:00",
    "events": {},
    "holidays": [
        # Зимние каникулы
        "2024-12-30",
        "2024-12-31",
        "2025-01-01",
        "2025-01-02",
        "2025-01-03",
        "2025-01-04",
        "2025-01-05",
        "2025-01-06",
        "2025-01-07",
        "2025-01-08",
        "2025-01-09",
        "2025-01-10",
        "2025-01-11",
        "2025-01-12",
        # Весенние каникулы
        "2025-03-22",
        "2025-03-23",
        "2025-03-24",
        "2025-03-25",
        "2025-03-26",
        "2025-03-27",
        "2025-03-28",
        "2025-03-29",
        "2025-03-30",
        "2025-03-31",
        # Летние каникулы
        *[
            f"2025-{month:02d}-{day:02d}"
            for month in range(6, 9)
            for day in range(1, 32)
        ],
    ],
}


# Проверка прав администратора
async def is_admin(user_id: int):
    return user_id in ADMIN_IDS


# Команда /start
@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    help_text = """
<b>Команды бота:</b>
/start или /help - это сообщение
/schedule - показать текущее расписание
/next_event - показать ближайшее событие

<b>Для администраторов:</b>
/change_day - изменить день занятий
/change_time - изменить время занятий
/add_event - добавить новое событие
/list_events - список всех событий
"""
    await message.answer(help_text, parse_mode=ParseMode.HTML)


# Показать расписание
@dp.message_handler(commands=["schedule"])
async def cmd_schedule(message: types.Message):
    days = [
        "понедельник",
        "вторник",
        "среда",
        "четверг",
        "пятница",
        "суббота",
        "воскресенье",
    ]
    text = (
        f"📅 <b>Текущее расписание:</b>\n"
        f"Занятия проходят каждую {days[schedule['default_day']]} в {schedule['default_time']}\n\n"
        f"<b>Ближайшие события:</b>\n"
    )

    if schedule["events"]:
        sorted_events = sorted(schedule["events"].items(), key=lambda x: x[1]["date"])
        for event_name, event_data in sorted_events[
            :3
        ]:  # Показываем 3 ближайших события
            text += f"- {event_name}: {event_data['date']} (напоминание за {event_data['reminder_days']} дн.)\n"
    else:
        text += "Нет запланированных событий"

    await message.answer(text, parse_mode=ParseMode.HTML)


# Изменить день занятий (только для админов)
@dp.message_handler(commands=["change_day"])
async def cmd_change_day(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("Эта команда доступна только администраторам")
        return

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    days = [
        "понедельник",
        "вторник",
        "среда",
        "четверг",
        "пятница",
        "суббота",
        "воскресенье",
    ]
    keyboard.add(*days)

    await message.answer("Выберите новый день для занятий:", reply_markup=keyboard)
    await ScheduleStates.waiting_for_day.set()


@dp.message_handler(state=ScheduleStates.waiting_for_day)
async def process_day_change(message: types.Message, state: FSMContext):
    days = [
        "понедельник",
        "вторник",
        "среда",
        "четверг",
        "пятница",
        "суббота",
        "воскресенье",
    ]
    if message.text.lower() not in days:
        await message.answer("Пожалуйста, выберите день из предложенных вариантов")
        return

    new_day = days.index(message.text.lower())
    schedule["default_day"] = new_day
    await state.finish()
    await message.answer(
        f"День занятий изменен на {message.text}",
        reply_markup=types.ReplyKeyboardRemove(),
    )


# Изменить время занятий (только для админов)
@dp.message_handler(commands=["change_time"])
async def cmd_change_time(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("Эта команда доступна только администраторам")
        return

    await message.answer(
        "Введите новое время занятий в формате ЧЧ:ММ (например, 15:00):"
    )
    await ScheduleStates.waiting_for_time.set()


@dp.message_handler(state=ScheduleStates.waiting_for_time)
async def process_time_change(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%H:%M")
        schedule["default_time"] = message.text
        await state.finish()
        await message.answer(f"Время занятий изменено на {message.text}")
    except ValueError:
        await message.answer(
            "Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ"
        )


# Добавить новое событие (только для админов)
@dp.message_handler(commands=["add_event"])
async def cmd_add_event(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("Эта команда доступна только администраторам")
        return

    await message.answer("Введите название события (например, 'Защита проектов'):")
    await ScheduleStates.waiting_for_event_name.set()


@dp.message_handler(state=ScheduleStates.waiting_for_event_name)
async def process_event_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["event_name"] = message.text

    await message.answer(
        "Введите дату события в формате ГГГГ-ММ-ДД (например, 2025-05-15):"
    )
    await ScheduleStates.waiting_for_event_date.set()


@dp.message_handler(state=ScheduleStates.waiting_for_event_date)
async def process_event_date(message: types.Message, state: FSMContext):
    try:
        event_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        async with state.proxy() as data:
            data["event_date"] = message.text

        await message.answer("За сколько дней напоминать о событии? (введите число):")
        await ScheduleStates.waiting_for_event_reminder.set()
    except ValueError:
        await message.answer(
            "Неверный формат даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД"
        )


@dp.message_handler(state=ScheduleStates.waiting_for_event_reminder)
async def process_event_reminder(message: types.Message, state: FSMContext):
    try:
        reminder_days = int(message.text)
        async with state.proxy() as data:
            event_name = data["event_name"]
            event_date = data["event_date"]

        schedule["events"][event_name] = {
            "date": event_date,
            "reminder_days": reminder_days,
            "reminder_sent": False,
        }

        await state.finish()
        await message.answer(
            f"Событие '{event_name}' добавлено на {event_date} с напоминанием за {reminder_days} дней"
        )
    except ValueError:
        await message.answer("Пожалуйста, введите число дней для напоминания")


# Список событий (только для админов)
@dp.message_handler(commands=["list_events"])
async def cmd_list_events(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("Эта команда доступна только администраторам")
        return

    if not schedule["events"]:
        await message.answer("Нет запланированных событий")
        return

    text = "📝 <b>Список событий:</b>\n"
    for event_name, event_data in schedule["events"].items():
        text += f"- {event_name}: {event_data['date']} (напоминание за {event_data['reminder_days']} дн.)\n"

    await message.answer(text, parse_mode=ParseMode.HTML)


# Ближайшее событие
@dp.message_handler(commands=["next_event"])
async def cmd_next_event(message: types.Message):
    if not schedule["events"]:
        await message.answer("Нет запланированных событий")
        return

    now = datetime.now().date()
    future_events = {
        k: v
        for k, v in schedule["events"].items()
        if datetime.strptime(v["date"], "%Y-%m-%d").date() >= now
    }

    if not future_events:
        await message.answer("Нет предстоящих событий")
        return

    next_event_name, next_event_data = min(
        future_events.items(),
        key=lambda x: datetime.strptime(x[1]["date"], "%Y-%m-%d").date(),
    )

    await message.answer(
        f"🗓 <b>Ближайшее событие:</b>\n"
        f"{next_event_name} - {next_event_data['date']}\n"
        f"Напоминание будет отправлено за {next_event_data['reminder_days']} дней",
        parse_mode=ParseMode.HTML,
    )


# Функции для напоминаний
async def send_reminder(chat_id, text):
    try:
        await bot.send_message(chat_id, text)
        logging.info(f"Reminder sent to {chat_id}: {text}")
    except Exception as e:
        logging.error(f"Error sending reminder to {chat_id}: {e}")


async def check_schedule():
    while True:
        now = datetime.now()
        today = now.date()

        # Проверка регулярных занятий
        if (
            now.weekday() == schedule["default_day"]
            and str(today) not in schedule["holidays"]
            and now.hour == 7
            and now.minute == 0
        ):

            await send_reminder(
                GROUP_CHAT_ID,
                f"🔔 Напоминание: сегодня занятие по КиберШколе в {schedule['default_time']}",
            )

        # Проверка выходных дней
        if str(today) in schedule["holidays"] and now.hour == 9 and now.minute == 0:
            await send_reminder(
                GROUP_CHAT_ID, "🌞 Напоминаю, что сегодня занятий не будет! Отдыхайте."
            )

        # Проверка событий
        for event_name, event_data in schedule["events"].items():
            event_date = datetime.strptime(event_data["date"], "%Y-%m-%d").date()
            reminder_date = event_date - timedelta(days=event_data["reminder_days"])

            if today == reminder_date and not event_data["reminder_sent"]:
                await send_reminder(
                    GROUP_CHAT_ID,
                    f"📢 Напоминание о событии '{event_name}' через {event_data['reminder_days']} дней ({event_data['date']})",
                )
                event_data["reminder_sent"] = True

            if today == event_date and now.hour == 9 and now.minute == 0:
                await send_reminder(
                    GROUP_CHAT_ID, f"🎉 Сегодня событие: {event_name}! Не пропустите!"
                )

        await asyncio.sleep(60)


# Запуск бота
async def on_startup(dp):
    asyncio.create_task(check_schedule())
    logging.info("Bot started")
