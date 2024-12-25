from difflib import SequenceMatcher
import logging

import aiosqlite
from aiogram.types import CallbackQuery
from sqlalchemy import MetaData
from sqlalchemy import select
from sqlalchemy import Table
from sqlalchemy import Column, Integer, String, DateTime, select, insert, update, delete, func, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from datetime import datetime, timedelta
from time import strftime

import texts
from config import *
import asyncio
import funcs
import config
from bot import bot

logging.getLogger('sqlalchemy.engine.Engine').disabled = True

Base = declarative_base()

class TelegramUser:
    def __init__(self, message):
        self.user_id = message.from_user.id
        self.username = message.from_user.username
        self.first_name = message.from_user.first_name
        self.message = message

    async def is_new(self) -> bool:
        async with Database() as db:
            return await db.is_new(self)

    async def is_banned(self) -> bool:
        async with Database() as db:
            return await db.is_banned(self)

    async def is_admin(self) -> bool:
        async with Database() as db:
            return await db.is_admin(self)


    async def update(self) -> None:
        async with Database() as db:
            await db.update_user(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return

class Database:
    def __init__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=True)

    async def __aenter__(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.engine.dispose()
        return

    async def easter_egg(self):
        async with self.engine.begin() as conn:
            await conn.execute(
                update(Teacher).where(Teacher.name == 'Сарайкин Алексей Анатольевич').values(
                    photo = 'https://i.ibb.co/8dxpJJx/5429192357452048425.jpg'
            ))

    async def get_channels(self):
        await self.update_events()
        async with self.engine.begin() as conn:
            result = await conn.execute(
                select(Channel)
            )
            channels = result.mappings().all()
            return channels

    async def add_channel(self, name, url):
        async with self.engine.begin() as conn:
            await conn.execute(insert(Channel).values(
                name = name,
                url = url,
            ))

    async def remove_channel(self, url):
        async with self.engine.begin() as conn:
            await conn.execute(delete(Channel).where(Channel.url == url))

    async def get_events(self):
        await self.update_events()
        async with self.engine.begin() as conn:
            result = await conn.execute(
                select(Event).where(Event.date >= func.now())
            )
            available_events = result.mappings().all()
            return available_events

    async def add_event(self, name, description, date, photo, repeat):
        async with self.engine.begin() as conn:
            await conn.execute(insert(Event).values(
                name = name,
                description = description,
                date = date,
                photo = photo,
                repeat = repeat
            ))
        await self.update_events()

    async def update_events(self):
        async with self.engine.begin() as conn:
            await conn.execute(
                update(Event).where(Event.date <= func.now() - timedelta(days=2), Event.repeat == 1).values(
                    date=Event.date + timedelta(days=365)  # GOOD
            ))
            await conn.execute(
                delete(Event).where(Event.date <= func.now() - timedelta(days=2), Event.repeat == 0))

    async def remove_event(self, id):
        async with self.engine.begin() as conn:
            await conn.execute(delete(Event).where(Event.id == id))

    async def get_event(self, id):
        async with self.engine.begin() as conn:
            result = await conn.execute(select(Event).where(Event.id == id))
            return result.mappings().one()

    async def update_teachers(self, user: TelegramUser):
        all_members = await funcs.parse_all_members()
        teachers = []
        for member in all_members:
            teachers.append(await funcs.parse_member_page(member['link']))
        teachers_names = [teacher['fio'] for teacher in teachers]
        async with self.engine.begin() as conn:
            result = await conn.execute(
                select(Teacher)
            )
            existing_teachers = result.fetchall()
            existing_teachers_names = [existing_teacher.name for existing_teacher in existing_teachers]
            for existing_teacher in existing_teachers:
                if existing_teacher.name not in teachers_names:
                    await conn.execute(delete(Teacher).where(Teacher.name == existing_teacher.name))
            for teacher in teachers:
                if teacher['fio'] not in existing_teachers_names:
                    await conn.execute(insert(Teacher).values(
                        name = teacher['fio'],
                        profession = teacher['profession'],
                        address = teacher['address'],
                        url = teacher['link'],
                        photo = teacher['photo']
                    ))
        async with Database() as db:
            await db.easter_egg()
        await bot.send_message(chat_id=user.user_id, text=texts.updated_teachers)

    async def find_teacher(self, name) -> [dict]:
        async with self.engine.begin() as conn:
            result = await conn.execute(
                select(Teacher)
            )
            all_teachers = result.mappings().all()
            match = [{'teacher': None, 'ratio': 0.0}]
            for teacher in all_teachers:
                ratio = SequenceMatcher(None, name.lower(), teacher.name.lower()).ratio()
                if ratio >= MATCH_THRESHOLD:
                    return [teacher]
                elif ratio > RATIO_THRESHOLD and ratio > match[-1]['ratio'] and teacher not in [m['teacher'] for m in match]:
                    match.append({'teacher': teacher, 'ratio': ratio})
                elif ratio > RATIO_THRESHOLD and ratio == match[-1]['ratio'] and teacher not in [m['teacher'] for m in match]:
                    match.append({'teacher': teacher, 'ratio': ratio})
            return [m['teacher'] for m in match[1:]]

    async def get_teacher_dict(self, id) -> [dict]:
        async with self.engine.begin() as conn:
            result = await conn.execute(
                select(Teacher).where(Teacher.id == int(id))
            )
            teacher = result.mappings().one()
            return teacher

    async def get_teacher_link(self, name) -> str:
        async with self.engine.begin() as conn:
            result = await conn.execute(
                select(Teacher).where(Teacher.name == name)
            )
            teacher = result.fetchone()
            return teacher.link

    async def is_new(self, telegram_user: TelegramUser) -> bool:
        async with self.engine.begin() as conn:
            result = await conn.execute(
                select(User).where(User.user_id == telegram_user.user_id)
            )
            user = result.fetchone()
            if not user:
                await self.add_new_user(telegram_user)
                return True
            else:
                return False

    async def is_admin(self, telegram_user: TelegramUser):
        if telegram_user.user_id == config.ADMIN_ID:
            return True
        async with self.engine.begin() as conn:
            result = await conn.execute(
                select(User).where(User.user_id == telegram_user.user_id)
            )
            user = result.fetchone()
            if not user:
                return False
            return user.admin == 1

    async def is_banned(self, telegram_user: TelegramUser):
        async with self.engine.begin() as conn:
            result = await conn.execute(
                select(User).where(User.user_id == telegram_user.user_id)
            )
            user = result.fetchone()
            if not user:
                return False
            return user.banned == 1


    async def update_user(self, telegram_user: TelegramUser):
        async with self.engine.begin() as conn:
            result = await conn.execute(
                select(User).where(User.user_id == telegram_user.user_id)
            )
            user = result.fetchone()
            if user.username != telegram_user.username or user.first_name != telegram_user.first_name:
                await conn.execute(update(User).where(User.user_id == telegram_user.user_id).values(
                    username=telegram_user.username,
                    first_name=telegram_user.first_name,
                    last_used=datetime.now(tz=TIMEZONE)
                ))
            await conn.execute(update(User).where(User.user_id == telegram_user.user_id).values(
                last_used=datetime.now(tz=TIMEZONE)
            ))
            return True

    async def add_new_user(self, telegram_user: TelegramUser):
        async with self.engine.begin() as conn:
            await conn.execute(insert(User).values(
                user_id=telegram_user.user_id,
                username=telegram_user.username,
                first_name=telegram_user.first_name
            ))
            return True


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, autoincrement=True, index=True, primary_key=True)
    user_id = Column(String, nullable=False)
    username = Column(String)
    first_name = Column(String, nullable=False)
    banned = Column(Integer, default=0)
    admin = Column(Integer, default=0)
    last_used = Column(DateTime, default=datetime.now(tz=TIMEZONE), onupdate=datetime.now(tz=TIMEZONE))
    first_used = Column(DateTime, default=datetime.now(tz=TIMEZONE))

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, autoincrement=True, index=True, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    photo = Column(String, default=None)
    repeat = Column(Integer, default=0)

class Channel(Base):
    __tablename__ = 'channels'

    id = Column(Integer, autoincrement=True, index=True, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)

class Teacher(Base):
    __tablename__ = 'teachers'
    id = Column(Integer, autoincrement=True, index=True, primary_key=True)
    name = Column(String, nullable=False)
    profession = Column(String, nullable=False)
    address = Column(String, nullable=False)
    photo = Column(String, nullable=False)
    url = Column(String, nullable=False)

