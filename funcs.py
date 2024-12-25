import aiohttp
import asyncio
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from config import *
import json
import aiofiles
import os

async def parse_member_page(link: str) -> dict:
    url = f'{KMB_URL}{link}'
    async with aiohttp.ClientSession() as session:
        async with await session.get(url, ssl=False) as resp:
            soup = BeautifulSoup(await resp.text(), 'html.parser')
            photo = soup.find('img', class_='photo_teacher')['src']
            fio = soup.find('div', class_='kris-component-head').text.strip()
            all_spans = soup.find_all('span', class_='title')
            for span in all_spans:
                if span.text == 'Занимаемая должность (должности):':
                    profession = span.find_next('span').text
                if span.text == 'Фактическое место работы':
                    address = span.find_next('span').text

    return {'fio': fio, 'photo': photo, 'profession': profession, 'address': address, 'link': link}

async def parse_all_members() -> [dict]:
    url = f'{KMB_URL}/o-nas/pedagogicheskii-sostav'
    result = []
    async with aiohttp.ClientSession() as session:
        async with await session.get(url, ssl=False) as resp:
            soup = BeautifulSoup(await resp.text(), 'html.parser')
            all_divs = soup.find_all('div', {'class': 'col-md-3 teacherblock'})
            for div in all_divs:
                a = div.find('a', {'class': 'fio'})
                fio = a.text.strip()
                link = a['href']
                result.append({'fio': fio, 'link': link})
    return result

async def find_member(input_name: str) -> [dict]:
    all_members = await parse_all_members()
    match = [{'member': None, 'ratio': 0.0}]
    for member in all_members:
        ratio = SequenceMatcher(None, input_name.lower(), member['fio'].lower()).ratio()
        if ratio >= MATCH_THRESHOLD:
            return [member]
        elif ratio > RATIO_THRESHOLD and ratio > match[-1]['ratio'] and member not in [m['member'] for m in match]:
            match.append({'member': member, 'ratio': ratio})
        elif ratio > RATIO_THRESHOLD and ratio == match[-1]['ratio'] and member not in [m['member'] for m in match]:
            match.append({'member': member, 'ratio': ratio})

async def parse_mosru_classes():
    url = MOSRU_URL
    headers = {
        'Authority': 'www.mos.ru',
        'Method': 'POST',
        'Path': '/pgu/common/ajax/index.php',
        'Scheme': 'https',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': 'mos_id=Cg+IA2ZN54qJ7B1AOAo+AgA=; PHPSESSID=69b0a6ecade272867a5b266d5557d056; _ym_uid=1733819561763915210; _ym_d=1733819561; _ym_isad=2; ACS-SESSID=nkd92o095eg04di8bt06kfboof; tmr_lvid=9e9cb2ff6aa733d04f2a7f9ccfe048d1; tmr_lvidTS=1733819563061; das_d_tag2=c6fccba8-c1b9-4dd2-b985-fb0740db9d60; das_d_tag2_legacy=c6fccba8-c1b9-4dd2-b985-fb0740db9d60; oxxfgh=1a4a2076-828b-474b-99c8-5efdd7944918%231%232592000000%2330000%23600000%2381540; uwyii=d9444ec1-0abc-8320-8c5b-9f661d28e074; domain_sid=JM93EXV-rFIQTsguJjwKq%3A1733819564434; oxxfghcd=1a4a2076-828b-474b-99c8-5efdd7944918#1#2592000000#30000#600000#81540; oxxfghcd_legacy=1a4a2076-828b-474b-99c8-5efdd7944918#1#2592000000#30000#600000#81540; tmr_detect=0%7C1733819645457; session-cookie=180fc3d0a6f704006baa3bb0beb261f5a05aba8ba7e45e5a4059af04dc615b43d7843ed78b87c775b3a7ab911520c639; uwyiert=6b57e4ea-938c-5d66-47a0-c74e9267fedf',
        'Origin': 'https://www.mos.ru',
        'Priority': 'u=1, i',
        'Referer': 'https://www.mos.ru/pgu/ru/app/depcult/077060701/',
        'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    all_items = []
    payload = MOSRU_PAYLOAD
    i = 1
    try:
        async with aiohttp.ClientSession() as session:
            while True:
                payload.update({'items[page]': f'{i}'})
                async with await session.post(url, data=payload, headers=headers, ssl=False) as resp:
                    data = json.loads(await resp.text())
                    items = data['result']['searchResItems']
                    if len(items) > 0:
                        all_items.extend(items)
                    if len(items) <= 0:
                        break
                    i += 1
        if all_items:
            return all_items
        else:
            return False
    except:
        return False

async def parse_mosru_class(id: int) -> dict:
    all_classes = await parse_mosru_classes()
    for class_ in all_classes:
        if class_['serviceId'] == id:
            return {'name': class_["programmShortName"], 'description': class_['description'], 'price': class_['financingDescription'], 'level': class_['educationType'], 'teacher': class_['organizationResourceType'][0]['name'], 'address': class_['organization']['address']['fullAddress'], 'schedule': class_['scheduleOfService'], 'phone_number': class_['organizationResourceType'][0]['phone']
}

async def get_schedule():
    if os.path.isfile(SCHEDULE_FILE):
        return SCHEDULE_FILE
    else:
        return False

async def main():
    name = input()
    members = await find_member(name)
    if members:
        if len(members) > 0:
            if len(members) > 2:
                print(members[-3:])
            else:
                print(await parse_member_page(members[-1]))
        else:
            print('Такое имя не найдено')
    else:
        print('Error')
    return

# asyncio.run(parse_mosru_classes())
