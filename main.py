import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from dotenv import load_dotenv

import json

load_dotenv()
TOKEN = os.getenv('TOKEN')
USER = os.getenv("USER")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

ADMINS = [int(USER)]

with open("venv/films.json", "r", encoding="utf-8") as file:
    films = json.load(file)


@dp.message_handler(commands='start')
async def start(message: types.Message):
    film_choice = InlineKeyboardMarkup()
    for film in films:
        button = InlineKeyboardButton(text=film, callback_data=film)
        film_choice.add(button)

    logging.info(
        f"Користувач {message.from_user.first_name} з нікнеймом {message.from_user.username} натиснув команду {message.text}")

    await message.answer(text='Привіт! Я кінобот🍿\n'
                              'Обери фільм, про який ти хочеш дізнатися.', reply_markup=film_choice)


@dp.callback_query_handler()
async def get_film_info(callback_query: types.CallbackQuery):
    if callback_query.data in films.keys():
        await bot.send_photo(callback_query.message.chat.id, films[callback_query.data]["photo"], "Постер фільму")
        url= films[callback_query.data]["site_url"]
        film_rating = films[callback_query.data]["rating"]
        film_description = films[callback_query.data]["description"]
        message = f"<b>Film url:</b> {url}\n\n<b>About:</b> {film_description}\n\n<b>Rate:</b> {film_rating}"
        await bot.send_message(callback_query.message.chat.id, message, parse_mode='html')
    else:
        await bot.send_message(callback_query.message.chat.id, 'Фільм не знайдено😟')


@dp.message_handler(commands='add_film')
async def add_new_film(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in ADMINS:
        await message.answer(text='Введи назву фільму, який ти хочеш додати.')
        await state.set_state('set_film_name')
    else:
        await message.answer(text='У Вас недостатньо прав для додавання нових фільмів.')

film_name = ''


@dp.message_handler(state='set_film_name')
async def set_film_name(message: types.Message, state: FSMContext):
    global film_name
    if len(message.text) > 64:
        message.answer(
            text='На жаль я не можу додати цей фільм, адже довжина його назви не має перевищувати 64 символи.')
    else:
        film_name = message.text
        films[film_name] = {}
        await state.set_state('set_site_url')
        await message.answer(text='Добре. Тепер введи посилання з інформацією на вебсайт.')


@dp.message_handler(state='set_site_url')
async def set_site_url(message: types.Message, state: FSMContext):
    global film_name
    film_site_url = message.text
    films[film_name]['site_url'] = film_site_url
    await state.set_state('set_description')
    await message.answer(text='Чудово. Розкажи щось цікаве про цей фільм.')


@dp.message_handler(state='set_description')
async def set_description(message: types.Message, state: FSMContext):
    global film_name
    film_description = message.text
    films[film_name]['description'] = film_description
    await state.set_state('set_rating')
    await message.answer(text='Чудово. Який рейтинг у цього фільма?')


@dp.message_handler(state='set_rating')
async def set_rating(message: types.Message, state: FSMContext):
    global film_name
    film_rating = message.text
    films[film_name]['rating'] = film_rating
    await state.set_state('set_photo')
    await message.answer(text='Чудово. Тепер дай посилання на банер цього фільм.')


@dp.message_handler(state='set_photo')
async def set_photo(message: types.Message, state: FSMContext):
    global film_name
    film_photo = message.text
    films[film_name]['photo'] = film_photo
    with open("venv/films.json", "w", encoding="utf-8") as file:
        json.dump(films, file, indent=4, ensure_ascii=False)
    print(films)
    await state.finish()
    await message.answer(text='Супер! Новий фільм успішно додано до бібліотеки.')


async def set_default_commands(dp):
    await bot.set_my_commands(
        [
            types.BotCommand('start', 'Запустити бота'),
            types.BotCommand('add_film', 'Додати новий фільм.')
        ]
    )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=set_default_commands)



