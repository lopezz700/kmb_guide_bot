from db import TelegramUser

error = 'Ошибка!'

# Menu texts
kb_get_schedule = '📅 Расписание'
kb_update_schedule = '🔄 Загрузить новое расписание'
kb_get_events = '🎉 Мероприятия'
kb_find_teacher = '👨‍🏫 Найти преподавателя'
kb_update_teachers = '🔄 Обновить базу преподавателей'
kb_classes = '📚 Кружки'

available_classes = 'Доступные кружки:'
available_events = 'Предстоящие мероприятия:'

enter_teachers_name_text = '👨‍🏫 Введите имя преподавателя:'
upload_new_schedule_text = '📁 Скиньте новое расписание в формате .xlsx:'
upload_new_schedule_success_text = '<b>Расписание было успешно загружено!</b> 🎉'

kb_back = 'Назад'
kb_page_back = '⬅️'
kb_page_forward = '➡️'

kb_contact = '📲 Написать'

# Faq texts
kb_info = '🤔 Информация'
kb_faq = '❓ FAQ'
info_text = '''<i>🤔 Информация:</i>

<b>📅 Расписание:</b>
Выводит актуальное расписание в формате Excel.

<b>🎉 Мероприятия:</b>
Показывает предстоящие мероприятия в колледже

<b>👨‍🏫 Найти преподавателя:</b>
Находит информацию о преподавателе по имени

<b>📚 Кружки:</b>
Показывает доступные кружки в колледже для записи
'''

faq_text = '''<i>❓ Ответы на часто задаваемые вопросы:</i>

<b>Где я могу найти информацию о заменах?</b>
Вся актуальная информация о заменах предоставлена в расписании.

<b>До какого числа мы учимся?</b>
Учебный процесс проходит с 1 сентября по 30 июня.
Межсеместровые каникулы с 29 декабря по 11 января.
Летние каникулы с 1 июля по 31 августа.

<b>Как найти преподавателя?</b>
Для поиска преподавателя вам достаточно ввести только часть его имени, а бот выдаст вам 3 наиболее похожих варианта.

<b>Как записаться на кружок?</b>
Для записи на кружок свяжитесь с контактным лицом, предоставленым в информации о кружке.

<b>Что делать, если нет ответа на мой вопрос?</b>
Если вы не нашли ответ на ваш вопрос, то можете задать его здесь: @username
'''

kb_add_channel = '➕ Добавить ссылку'
kb_delete_channel = '🚫 Удалить ссылку'
new_channel_name = '📝 Введите название ссылки:'
new_channel_url = '📊 Введите ссылку:'
new_channel_added = '<b>Ссылка была успешно добавлена!</b> 🎉'
new_channel_error = '<b>Ошибка при добавлении новой ссылки!</b> 🚫'
delete_channel_error = '<b>Ошибка при удалении ссылки!</b> 🚫'
delete_channel_url = '📊 Введите ссылку для удаления:'
channel_removed_text = '<b>Ссылка была успешно удалена!</b> 🎉'

# Events texts
add_event = '➕ Добавить мероприятие'
remove_event = '🚫 Удалить мероприятие'
add_event_requirements = f'''
<b>Введите:</b>
<i>Название мероприятия</i>
<i>Описание</i>
<i>Дату (день.месяц.год чч:мм)</i>
<i>Будет ли мероприятие повторяться в след. году (1 или 0)</i>
<i>Прикрепите фото (Необязательно)</i>

Пример:
<i>1 Сентября</i>
<i>Начало нового учебного года для наших студентов и преподавателей.</i>
<i>01.09.2024 09:00</i>
<i>1</i>
'''
event_added = '<b>Мероприятие было успешно добавлено!</b> 🎉'
kb_delete_event = '🚫 Удалить мероприятие'
event_deleted = '<b>Мероприятие было успешно удалено!</b> 🎉'
new_event_error = '<b>Ошибка при добавлении нового мероприятия!</b> 🚫'

# Find teacher texts
teachers_found = 'Возможно вы имели ввиду:'
teacher_not_found = '<b>Данный преподаватель не был найден</b> 🤔'
updating_teachers = '<b>База преподавателей обновляется...</b> 🔄'
updated_teachers = '<b>База преподавателей обновлена!</b> 🎉'

async def event_text(event: dict) -> str:
    result = f'''
<b>{event['name']}</b>
{event['description']}

<i>{event['date'].strftime('%d.%m.%Y')}</i>
<i>{event['date'].strftime('%H:%M')}</i>
'''
    return result

async def class_text(class_: dict) -> str:
    result = f'''
<b>{class_['name']}</b>

{class_['description']}

Цена: <i>{class_['price']}</i>
Расписание: <i>{class_['schedule']}</i>

Контактное лицо: <i>{class_['teacher']}</i>
<i>{class_['phone_number']}</i>
'''
    return result

async def teacher_info_text(teacher: dict) -> str:
    result = f'''
<b>{teacher['name']}</b>

Должность: <i>{teacher['profession']}</i>
Место работы: <i>{teacher['address']}</i>
'''
    return result

async def welcome_text(user: TelegramUser) -> str:
    result = f'''
<b>Добро пожаловать в КМБ №4, {user.first_name}!</b>
Мы рады видеть тебя в нашем колледже!
'''
    return result

async def start_text(user: TelegramUser) -> str:
    result = f'''
<b>Привет, {user.first_name}!</b>

Это твой личный гид по КМБ №4.
Здесь ты можешь найти расписание, мероприятия, кружки и многое другое.
'''
    return result

