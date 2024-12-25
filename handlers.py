from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender

from bot import bot
import texts
from config import TYPING_TIMEOUT, KMB_URL, SCHEDULE_FILE, ITEMS_PER_PAGE, TIMEZONE
from db import TelegramUser, Database
import keyboards
import funcs

import aiofiles
import asyncio
import math
from datetime import datetime
import pytz

router = Router()

class FindTeacher(StatesGroup):
    name = State()

class UploadSchedule(StatesGroup):
    document = State()

class NewEvent(StatesGroup):
    event = State()

class NewChannel(StatesGroup):
    name = State()
    url = State()

class DeleteChannel(StatesGroup):
    url = State()

async def checks(user: TelegramUser):
    await user.update()
    if await user.is_banned():
        print(f'User {user.username} is banned!')
        return False
    if str(user.user_id)[:2] == '-1':
        print('Group chat!')
        return False
    return True

@router.message(Command('start'))
async def start_handler(msg: Message):
    async with TelegramUser(msg) as user:
        if await user.is_new():
            await msg.answer(await texts.welcome_text(user), reply_markup=await keyboards.start_kb(user))
            return

        if not await checks(user):
            return

        else:
            await msg.answer(await texts.start_text(user), reply_markup=await keyboards.start_kb(user))

# States
@router.message(F.text, FindTeacher.name)
async def fsm_find_teacher_handler(msg: Message, state: FSMContext):
    async with TelegramUser(msg) as user:
        if not await checks(user):
            return

        async with ChatActionSender.typing(msg.chat.id, bot):
            await asyncio.sleep(TYPING_TIMEOUT)
            await state.update_data(name=msg.text)
            data = await state.get_data()
            async with Database() as db:
                result: [dict] = await db.find_teacher(data['name'])
                if result:
                    if len(result) > 0:
                        if len(result) > 2:
                            await bot.send_message(chat_id=user.user_id, text=texts.teachers_found, reply_markup=await keyboards.teachers_kb(result[-3:]))
                        else:
                            result = result[0]
                            if '://' in result['photo']:
                                photo_url = result['photo']
                            else:
                                photo_url = KMB_URL + result['photo']
                            await bot.send_photo(chat_id=user.user_id, photo=photo_url, caption=await texts.teacher_info_text(result), reply_markup=await keyboards.back_kb('menu'))

                else:
                    await bot.send_message(chat_id=user.user_id, text=texts.teacher_not_found)
                    await bot.send_message(chat_id=user.user_id, text=texts.enter_teachers_name_text, reply_markup=await keyboards.back_kb('menu'))
                    await state.set_state(FindTeacher.name)
            await state.clear()


@router.message(F.document, UploadSchedule.document)
async def fsm_upload_schedule(msg: Message, state: FSMContext):
    async with TelegramUser(msg) as user:
        if not await checks(user):
            return

        await state.update_data(name=msg.text)
        document_id = msg.document.file_id
        await state.update_data(document=document_id)
        data = await state.get_data()
        file = await bot.get_file(data['document'])
        file_path = file.file_path
        await bot.download_file(file_path, SCHEDULE_FILE)
        await bot.send_message(chat_id=user.user_id, text=texts.upload_new_schedule_success_text)
        await msg.answer(await texts.start_text(user), reply_markup=await keyboards.start_kb(user))
        await state.clear()


@router.message(F.text, NewEvent.event)
async def fsm_new_event(msg: Message, state: FSMContext):
    async with TelegramUser(msg) as user:
        if not await checks(user):
            return

        async with ChatActionSender.typing(msg.chat.id, bot):
            await state.update_data(event=msg)
            data = await state.get_data()
            data = data['event']

            args = data.text.split('\n')
            name = args[0]
            description = args[1]
            try:
                date = datetime.strptime(args[2], "%d.%m.%Y %H:%M")
                date = date.replace(tzinfo=TIMEZONE)
            except:
                await bot.send_message(chat_id=user.user_id, text=texts.new_event_error)
                return
            repeat = args[3]

            async with Database() as db:
                await db.add_event(name, description, date, None, repeat)

            await bot.send_message(chat_id=user.user_id, text=texts.event_added)
            async with Database() as db:
                events = await db.get_events()
                if len(events) == 0:
                    pages = 1
                else:
                    pages = math.ceil(len(events) / ITEMS_PER_PAGE)
                await bot.send_message(chat_id=user.user_id, text=texts.available_events, reply_markup=await keyboards.events_kb(events, 1, pages, user))
            await state.clear()

@router.message(F.photo, NewEvent.event)
async def fsm_new_event_with_photo(msg: Message, state: FSMContext):
    async with TelegramUser(msg) as user:
        if not await checks(user):
            return

        async with ChatActionSender.typing(msg.chat.id, bot):
            await state.update_data(event=msg)
            data = await state.get_data()
            data = data['event']

            photo = data.photo[-1]
            file_id = photo.file_id
            args = data.caption.split('\n')
            if len(args) < 4:
                await bot.send_message(chat_id=user.user_id, text=texts.new_event_error)
            name = args[0]
            description = args[1]
            try:
                date = datetime.strptime(args[2], "%d.%m.%Y %H:%M")
                date = date.replace(tzinfo=TIMEZONE)
            except:
                await bot.send_message(chat_id=user.user_id, text=texts.new_event_error)
                return
            repeat = args[3]

            if date < datetime.now(tz=TIMEZONE):
                await bot.send_message(chat_id=user.user_id, text=texts.new_event_error)

            async with Database() as db:
                await db.add_event(name, description, date, file_id, repeat)

            await bot.send_message(chat_id=user.user_id, text=texts.event_added)
            async with Database() as db:
                events = await db.get_events()
                if len(events) == 0:
                    pages = 1
                else:
                    pages = math.ceil(len(events) / ITEMS_PER_PAGE)
                await bot.send_message(chat_id=user.user_id, text=texts.available_events, reply_markup=await keyboards.events_kb(events, 1, pages, user))
            await state.clear()

@router.message(F.text, NewChannel.name)
async def fsm_new_channel_name(msg: Message, state: FSMContext):
    async with TelegramUser(msg) as user:
        if not await checks(user):
            return

        await state.update_data(name=msg.text)
        await bot.send_message(chat_id=user.user_id, text=texts.new_channel_url, reply_markup=await keyboards.back_kb('channels'))
        await state.set_state(NewChannel.url)

@router.message(F.text, NewChannel.url)
async def fsm_new_channel_link(msg: Message, state: FSMContext):
    async with TelegramUser(msg) as user:
        if not await checks(user):
            return

        async with ChatActionSender.typing(msg.chat.id, bot):
            if not '://' in msg.text:
                await bot.send_message(chat_id=user.user_id, text=texts.new_channel_error)
                await state.clear()
                return

            await state.update_data(url=msg.text)
            data = await state.get_data()
            async with Database() as db:
                await db.add_channel(data['name'], data['url'])
            await bot.send_message(chat_id=user.user_id, text=texts.new_channel_added)
            await bot.send_message(chat_id=user.user_id, text=texts.info_text, reply_markup=await keyboards.faq_kb(user))
            await state.clear()

@router.message(F.text, DeleteChannel.url)
async def fsm_new_channel_link(msg: Message, state: FSMContext):
    async with TelegramUser(msg) as user:
        if not await checks(user):
            return

        async with ChatActionSender.typing(msg.chat.id, bot):
            if not '://' in msg.text:
                await bot.send_message(chat_id=user.user_id, text=texts.delete_channel_error)
                await state.clear()
                return

            await state.update_data(url=msg.text)
            data = await state.get_data()
            async with Database() as db:
                await db.remove_channel(data['url'])
            await bot.send_message(chat_id=user.user_id, text=texts.channel_removed_text)
            await bot.send_message(chat_id=user.user_id, text=texts.info_text, reply_markup=await keyboards.faq_kb(user))
            await state.clear()

# Callbacks
@router.callback_query()
async def callback_handler(cb: CallbackQuery, state: FSMContext):
    data = cb.data
    args = data.split(':')
    print(f'Args: {args}')
    async with TelegramUser(cb) as user:
        if not await checks(user):
            return

        await state.clear()


        if args[0] == 'back':
            await state.set_state(None)
            if args[1] == 'menu' or args[1] == 'teacher':
                    try:
                        await cb.message.edit_text(await texts.start_text(user), reply_markup=await keyboards.start_kb(user))
                    except TelegramBadRequest:
                        await bot.delete_message(cb.from_user.id, cb.message.message_id)
                        await bot.send_message(chat_id=user.user_id, text=await texts.start_text(user), reply_markup=await keyboards.start_kb(user))
            if args[1] == 'events':
                async with Database() as db:
                    events = await db.get_events()
                    if len(events) == 0:
                        pages = 1
                    else:
                        pages = math.ceil(len(events) / ITEMS_PER_PAGE)
                    await cb.message.edit_text(text=texts.available_events, reply_markup=await keyboards.events_kb(events, 1, pages, user))
            if args[1] == 'event':
                async with Database() as db:
                    events = await db.get_events()
                    if len(events) == 0:
                        pages = 1
                    else:
                        pages = math.ceil(len(events) / ITEMS_PER_PAGE)
                    await bot.delete_message(chat_id=user.user_id, message_id=cb.message.message_id)
                    await bot.send_message(chat_id=user.user_id, text=texts.available_events, reply_markup=await keyboards.events_kb(events, 1, pages, user))
            if args[1] == 'channels':
                await cb.message.edit_text(text=texts.info_text, reply_markup=await keyboards.faq_kb(user))

        elif args[1] == 'teacher':
            async with Database() as db:
                teacher = await db.get_teacher_dict(args[2])
                await bot.delete_message(cb.from_user.id, cb.message.message_id)
                if '://' in teacher['photo']:
                    photo_url = teacher['photo']
                else:
                    photo_url = KMB_URL + teacher['photo']
                await bot.send_photo(chat_id=user.user_id, photo=photo_url, caption=await texts.teacher_info_text(teacher), reply_markup=await keyboards.back_kb(args[0]))

        elif args[1] == 'events':
            if args[2] == 'page':
                async with Database() as db:
                        events = await db.get_events()
                        if len(events) == 0:
                            pages = 1
                        else:
                            pages = math.ceil(len(events) / ITEMS_PER_PAGE)
                        try:
                            await cb.message.edit_text(text=texts.available_events, reply_markup=await keyboards.events_kb(events, int(args[3]), pages, user))
                        except TelegramBadRequest:
                            pass

        elif args[1] == 'event':
            if args[2] == 'add' and await user.is_admin():
                await cb.message.edit_text(text=texts.add_event_requirements, reply_markup=await keyboards.back_kb(args[0]))
                await state.set_state(NewEvent.event)
            if args[2] == 'show':
                async with Database() as db:
                    event = await db.get_event(int(args[3]))
                    if event.photo:
                        await bot.delete_message(chat_id=user.user_id, message_id=cb.message.message_id)
                        await bot.send_photo(chat_id=user.user_id, photo=event.photo, caption=await texts.event_text(event), reply_markup=await keyboards.event_kb(int(args[3]), user))
                    else:
                        await bot.delete_message(chat_id=user.user_id, message_id=cb.message.message_id)
                        await bot.send_message(chat_id=user.user_id, text=await texts.event_text(event), reply_markup=await keyboards.event_kb(args[3], user))
            if args[2] == 'delete':
                async with Database() as db:
                    await db.remove_event(int(args[3]))
                    events = await db.get_events()
                    if len(events) == 0:
                        pages = 1
                    else:
                        pages = math.ceil(len(events) / ITEMS_PER_PAGE)
                    await bot.delete_message(chat_id=user.user_id, message_id=cb.message.message_id)
                    await bot.send_message(chat_id=user.user_id, text=texts.event_deleted)
                    await bot.send_message(chat_id=user.user_id, text=texts.available_events, reply_markup=await keyboards.events_kb(events, 1, pages, user))

        elif args[1] == 'schedule':
            file_path = await funcs.get_schedule()
            if file_path:
                await bot.delete_message(cb.from_user.id, cb.message.message_id)
                await bot.send_document(cb.from_user.id, FSInputFile(file_path))
                await bot.send_message(chat_id=user.user_id, text=await texts.start_text(user), reply_markup=await keyboards.start_kb(user))
            else:
                await cb.answer(texts.error)

        elif args[1] == 'upload_schedule':
            await cb.message.edit_text(text=texts.upload_new_schedule_text, reply_markup=await keyboards.back_kb(args[0]))
            await state.set_state(UploadSchedule.document)

        elif args[1] == 'find_teacher':
            await cb.message.edit_text(text=texts.enter_teachers_name_text, reply_markup=await keyboards.back_kb(args[0]))
            await state.set_state(FindTeacher.name)

        elif args[1] == 'update_teachers':
            async with ChatActionSender.typing(cb.from_user.id, bot):
                await bot.send_message(chat_id=user.user_id, text=texts.updating_teachers)
                async with Database() as db:
                    await db.update_teachers(user)

        elif args[1] == 'classes':
            if args[2] == 'page':
                async with ChatActionSender.typing(cb.from_user.id, bot):
                    all_classes = await funcs.parse_mosru_classes()
                    all_classes = all_classes[::2]
                    pages = math.ceil(len(all_classes) / ITEMS_PER_PAGE)
                    try:
                        await cb.message.edit_text(text=texts.available_classes, reply_markup=await keyboards.classes_kb(all_classes, int(args[3]), pages))
                    except TelegramBadRequest:
                        pass

        elif args[1] == 'class':
            if args[2] == 'show':
                async with ChatActionSender.typing(cb.from_user.id, bot):
                    class_ = await funcs.parse_mosru_class(int(args[3]))
                    await cb.message.edit_text(text=await texts.class_text(class_), reply_markup=await keyboards.class_kb(class_))

        elif args[1] == 'channel':
            if args[2] == 'show':
                await cb.message.edit_text(text=texts.info_text, reply_markup=await keyboards.faq_kb(user))
            if args[2] == 'add':
                await bot.send_message(chat_id=user.user_id, text=texts.new_channel_name, reply_markup=await keyboards.back_kb(args[0]))
                await state.set_state(NewChannel.name)
            if args[2] == 'delete':
                await bot.send_message(chat_id=user.user_id, text=texts.delete_channel_url, reply_markup=await keyboards.back_kb(args[0]))
                await state.set_state(DeleteChannel.url)
            if args[2] == 'faq':
                await cb.message.edit_text(text=texts.faq_text, reply_markup=await keyboards.back_kb(args[0]))
