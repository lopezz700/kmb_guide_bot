import pytz
import os

# admin
ADMIN_ID = 123

# bot
BOT_TOKEN = ''
TYPING_TIMEOUT = 0.6

# parsing
KMB_URL = 'https://kmb-4.mskobr.ru'
MOSRU_URL = 'https://www.mos.ru/pgu/common/ajax/index.php'
MOSRU_PAYLOAD = {
    'ajaxModule': 'Esz',
    'ajaxAction': 'startSearch',
    'items[organizationId]': '10431',
    'items[isOpen]': '1',
    # 'items[page]': '1'
}
ITEMS_PER_PAGE = 3

# database
DATABASE_URL = 'sqlite+aiosqlite:///./database.db'

# files
FILES_FOLDER = 'Files'
SCHEDULE_FILE = f'{FILES_FOLDER}/Расписание.xlsx'
SCHEDULE_IMG_FILE = f'{FILES_FOLDER}/Расписание.png'

# funcs
RATIO_THRESHOLD = 0.25
MATCH_THRESHOLD = 0.75

# misc
TIMEZONE = pytz.timezone('Europe/Moscow')
