import asyncio
from bot import bot
from handlers import router
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import logging
from db import Database

logging.basicConfig(level=logging.INFO)

async def start():
    print('Bot has started!')
    # Use to update teachers database
    # async with Database() as db:
    #     await db.update_teachers()

async def stop():
    print('Bot has stopped')

async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.startup.register(start)
    dp.shutdown.register(stop)
    dp.include_router(router)
    async with Database() as db:
        await db.easter_egg()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
