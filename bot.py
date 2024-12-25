from aiogram import Bot, Router, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from config import BOT_TOKEN

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()
