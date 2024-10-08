import aiohttp
import disnake

WEEKDAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']


async def async_request(url: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.content.read()
    except:
        pass


def get_day_by_date(date, days: list):
    for day in days:
        if date == day.date:
            return day


def get_channel_or_user_id(inter: disnake.MessageInteraction | disnake.ApplicationCommandInteraction):
    if inter.guild_id:
        return inter.channel_id
    else:
        return inter.user.id


async def send_message_by_chats(bot, chats: list, *args, **kwargs):
    for chat in chats:
        if chat.guild_id:
            channel = bot.get_guild(chat.guild_id)
            if channel:
                channel = channel.get_channel(chat.channel_id)
        else:
            channel = bot.get_user(chat.channel_id)
        if channel:
            await channel.send(*args, **kwargs)


def get_lesson_by_index(index: int, lessons: list):
    for index_, lesson in enumerate(lessons):
        if index_ == index:
            return lesson


def edited_or_no(field, new_indexes):
    return "(Изменено)" if field in new_indexes else ""


def get_new_content_indexes(new_lesson, old_lesson):
    indexes = []
    if old_lesson:
        for content_name, content in new_lesson:
            if content != old_lesson.dict()[content_name]:
                indexes.append(content_name)
    return indexes


def get_lesson_embed(day, lesson, college_url, group_name, group_url, new_content_indexes: list = []):
    cvh = disnake.Embed(title=f"{WEEKDAYS[int(day.date.strftime('%w')) - 1]} {day.date.strftime('%d.%m.%Y')}",
                        color=lesson.bgcolor)
    cvh.set_author(name=f"Расписание занятий | {group_name}", url=college_url + group_url)
    cvh.set_footer(text=f"Источник: {college_url}")
    cvh.add_field(name=f'№ пары {edited_or_no("number", new_content_indexes)}', value=lesson.number)
    cvh.add_field(name=f'Время занятий {edited_or_no("timeline", new_content_indexes)}', value=lesson.timeline)
    cvh.add_field(name=f'Способ {edited_or_no("process_type", new_content_indexes)}', value=lesson.process_type)
    cvh.add_field(name=f'Дисциплина, преподаватель {edited_or_no("discipline", new_content_indexes)}', value=lesson.discipline)
    if lesson.theme:
        cvh.add_field(name=f'Тема занятия {edited_or_no("theme", new_content_indexes)}', value=lesson.theme)
    if lesson.resources:
        cvh.add_field(name=f'Ресурс {edited_or_no("resources", new_content_indexes)}', value=lesson.resources)
    if lesson.tasks:
        cvh.add_field(name=f'Задание для выполнения {edited_or_no("tasks", new_content_indexes)}', value=lesson.tasks)

    return cvh


def parting(array: list, numparts: int):
    new_array = []
    for index, obj in enumerate(array):
        if index % numparts == 0:
            new_array.append([obj])
        else:
            new_array[-1].append(obj)
    return new_array
