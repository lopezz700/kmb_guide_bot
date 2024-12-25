from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db import TelegramUser, Database
import texts
from config import ITEMS_PER_PAGE

async def start_kb(user: TelegramUser):
    builder = InlineKeyboardBuilder()
    is_admin = await user.is_admin()

    builder.row(
        InlineKeyboardButton(text=texts.kb_get_schedule, callback_data='menu:schedule'),
        InlineKeyboardButton(text=texts.kb_get_events, callback_data='menu:events:page:1'),
        width=2
    )

    if is_admin:
        builder.row(
            InlineKeyboardButton(text=texts.kb_update_schedule, callback_data='menu:upload_schedule'),
            width=1
    )

    builder.row(
        InlineKeyboardButton(text=texts.kb_find_teacher, callback_data='menu:find_teacher'),
        width=1
    )

    if is_admin:
        builder.row(
            InlineKeyboardButton(text=texts.kb_update_teachers, callback_data='menu:update_teachers'),
            width=1
        )

    builder.row(
        InlineKeyboardButton(text=texts.kb_classes, callback_data='menu:classes:page:1'),
        width=1
    )

    builder.row(
        InlineKeyboardButton(text=texts.kb_info, callback_data='channels:channel:show'),
        width=1
    )

    return builder.as_markup()

async def faq_kb(user: TelegramUser):
    builder = InlineKeyboardBuilder()
    is_admin = await user.is_admin()

    async with Database() as db:
        channels = await db.get_channels()

    for i in range(0, len(channels), 2):
        channel_1 = channels[i]
        channel_2 = channels[i + 1] if i + 1 < len(channels) else None
        if channel_2:
            builder.row(
                InlineKeyboardButton(text=channel_1['name'], url=channel_1['url']),
                InlineKeyboardButton(text=channel_2['name'], url=channel_2['url']),
                width=2
            )
        else:
            builder.row(
                InlineKeyboardButton(text=channel_1['name'], url=channel_1['url']),
                width=1
            )

    builder.row(
        InlineKeyboardButton(text=texts.kb_faq, callback_data='channels:channel:faq'),
        width=1
    )

    if is_admin:
        builder.row(
            InlineKeyboardButton(text=texts.kb_add_channel, callback_data='menu:channel:add'),
            InlineKeyboardButton(text=texts.kb_delete_channel, callback_data='menu:channel:delete'),
            width=2
        )

    builder.row(
        InlineKeyboardButton(text=texts.kb_back, callback_data='back:menu'),
        width=1
    )

    return builder.as_markup()

async def teachers_kb(teachers: [dict]):
    builder = InlineKeyboardBuilder()
    for teacher in teachers[::-1]:
        builder.row(
            InlineKeyboardButton(text=teacher['name'], callback_data=f'menu:teacher:{teacher["id"]}'),
            width=1
        )
    return builder.as_markup()

async def event_kb(event_id, user: TelegramUser):
    builder = InlineKeyboardBuilder()
    is_admin = await user.is_admin()

    if is_admin:
        builder.row(
            InlineKeyboardButton(text=texts.kb_delete_event, callback_data=f'events:event:delete:{event_id}')
        )

    builder.row(
        InlineKeyboardButton(text=texts.kb_back, callback_data=f'back:event'),
        width=1
    )
    return builder.as_markup()

async def events_kb(events: dict, page, max_page, user: TelegramUser):
    builder = InlineKeyboardBuilder()
    is_admin = await user.is_admin()

    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE

    page_text = f'{page}/{max_page}'

    for event in events[start:end]:
        builder.row(
            InlineKeyboardButton(text=event['name'], callback_data=f'events:event:show:{event["id"]}'),
            width=1
        )

    if is_admin:
        builder.row(
            InlineKeyboardButton(text=texts.add_event, callback_data='events:event:add')
        )

    if page <= 1 and page != max_page:
        builder.row(
            InlineKeyboardButton(text=texts.kb_page_back, callback_data=f'menu:events:page:{max_page}'),
            InlineKeyboardButton(text=page_text, callback_data=f':'),
            InlineKeyboardButton(text=texts.kb_page_forward, callback_data=f'menu:events:page:{page + 1}'),
            width=3
        )

    elif page <= 1 and page >= max_page:
        builder.row(
            InlineKeyboardButton(text=texts.kb_page_back, callback_data=f'menu:events:page:{max_page}'),
            InlineKeyboardButton(text=page_text, callback_data=f':'),
            InlineKeyboardButton(text=texts.kb_page_forward, callback_data=f'menu:events:page:{page}'),
            width=3
        )

    elif page > 1 and not page >= max_page:
        builder.row(
            InlineKeyboardButton(text=texts.kb_page_back, callback_data=f'menu:events:page:{page - 1}'),
            InlineKeyboardButton(text=page_text, callback_data=f':'),
            InlineKeyboardButton(text=texts.kb_page_forward, callback_data=f'menu:events:page:{page + 1}'),
            width=3
        )

    elif page > 1 and page >= max_page:
        builder.row(
            InlineKeyboardButton(text=texts.kb_page_back, callback_data=f'menu:events:page:{page - 1}'),
            InlineKeyboardButton(text=page_text, callback_data=f':'),
            InlineKeyboardButton(text=texts.kb_page_forward, callback_data=f'menu:events:page:1'),
            width=3
        )

    builder.row(InlineKeyboardButton(text=texts.kb_back, callback_data=f'back:menu', width=1))
    return builder.as_markup()

async def class_kb(class_: dict):
    builder = InlineKeyboardBuilder()
    phone = class_["phone_number"].replace(' ', '').replace('-', '').replace('(', '').replace(')', '').strip()

    builder.row(
        InlineKeyboardButton(text=texts.kb_contact, url=f'https://wa.me/{phone}'),
        width=1
    )

    builder.row(InlineKeyboardButton(text=texts.kb_back, callback_data=f'menu:classes:page:1', width=1))
    return builder.as_markup()

async def classes_kb(classes: [dict], page, max_page):
    builder = InlineKeyboardBuilder()

    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE

    page_text = f'{page}/{max_page}'

    for class_ in classes[start:end]:
        builder.row(
            InlineKeyboardButton(text=class_["programmShortName"], callback_data=f'menu:class:show:{class_["serviceId"]}'),
            width=1
        )



    if page <= 1 and page != max_page:
        builder.row(
            InlineKeyboardButton(text=texts.kb_page_back, callback_data=f'menu:classes:page:{max_page}'),
            InlineKeyboardButton(text=page_text, callback_data=f':'),
            InlineKeyboardButton(text=texts.kb_page_forward, callback_data=f'menu:classes:page:{page + 1}'),
            width=3
        )

    if page <= 1 and page >= max_page:
        builder.row(
            InlineKeyboardButton(text=texts.kb_page_back, callback_data=f'menu:classes:page:{max_page}'),
            InlineKeyboardButton(text=page_text, callback_data=f':'),
            InlineKeyboardButton(text=texts.kb_page_forward, callback_data=f'menu:classes:page:{page}'),
            width=3
        )

    elif page > 1 and not page >= max_page:
        builder.row(
            InlineKeyboardButton(text=texts.kb_page_back, callback_data=f'menu:classes:page:{page - 1}'),
            InlineKeyboardButton(text=page_text, callback_data=f':'),
            InlineKeyboardButton(text=texts.kb_page_forward, callback_data=f'menu:classes:page:{page + 1}'),
            width=3
        )

    elif page > 1 and page >= max_page:
        builder.row(
            InlineKeyboardButton(text=texts.kb_page_back, callback_data=f'menu:classes:page:{page - 1}'),
            InlineKeyboardButton(text=page_text, callback_data=f':'),
            InlineKeyboardButton(text=texts.kb_page_forward, callback_data=f'menu:classes:page:1'),
            width=3
        )

    builder.row(InlineKeyboardButton(text=texts.kb_back, callback_data=f'back:menu', width=1))

    return builder.as_markup()

async def back_kb(arg):
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text=texts.kb_back, callback_data=f'back:{arg}'),
        width=1
    )
    return builder.as_markup()
