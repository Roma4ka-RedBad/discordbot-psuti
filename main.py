import disnake
from disnake.ext import commands, tasks
from models import GroupsView, WeekdaysView
from utils import get_day_by_date, get_lesson_by_index, get_lesson_embed, get_channel_or_user_id, send_message_by_chats, get_new_content_indexes, DATABASE
from database import Database
from college import CollegeDesc

bot = commands.Bot(command_prefix='/', intents=disnake.Intents.all(), reload=True)
college = CollegeDesc()
database = Database(college, DATABASE)


@tasks.loop(seconds=15)
async def week_handler():
    try:
        for group_name, group_obj in database.groups_by_handlers.copy().items():
            new_total_week = (await college.get_desc_by_url(group_obj.total_week_obj.total_week_href)).get_week()
            if new_total_week != group_obj.total_week_obj:
                print(f"[{group_name}] Новые изменения в расписании!")
                if group_obj.total_week_obj.start_date != new_total_week.start_date:
                    print(f"    [{group_name}] Смена недели!")
                    # await send_message_by_chats(bot, group_obj.chats, content="_Новая неделя наступила! Ложимся спать, завтра в садик!_")
                else:
                    print(f"    [{group_name}] Смена событий!")
                    for day in new_total_week.days:
                        founded_day = get_day_by_date(day.date, group_obj.total_week_obj.days)
                        if day != founded_day:
                            for index, lesson in enumerate(day.lessons):
                                old_lesson = get_lesson_by_index(index, founded_day.lessons)
                                if lesson != old_lesson:
                                    cvh = get_lesson_embed(day, lesson, college.url, group_name, new_total_week.total_week_href, get_new_content_indexes(lesson, old_lesson))
                                    await send_message_by_chats(bot, group_obj.chats, content="_Заметил изменения в паре на этой неделе!_", embed=cvh)
                database.groups_by_handlers[group_name].total_week_obj = new_total_week

            new_next_week = (await college.get_desc_by_url(group_obj.total_week_obj.next_week_href)).get_week()
            if new_next_week != group_obj.next_week_obj:
                print(f"[{group_name}] Новые изменения в расписании!")
                if group_obj.next_week_obj.start_date == new_next_week.start_date:
                    print(f"    [{group_name}] Смена событий!")
                    for day in new_next_week.days:
                        founded_day = get_day_by_date(day.date, group_obj.next_week_obj.days)
                        if day != founded_day:
                            for index, lesson in enumerate(day.lessons):
                                old_lesson = get_lesson_by_index(index, founded_day.lessons)
                                if lesson != old_lesson:
                                    cvh = get_lesson_embed(day, lesson, college.url, group_name, new_next_week.total_week_href, get_new_content_indexes(lesson, old_lesson))
                                    await send_message_by_chats(bot, group_obj.chats, content="_Заметил изменения в паре на следующей неделе!_", embed=cvh)
                database.groups_by_handlers[group_name].next_week_obj = new_next_week
    except Exception as err:
        print(err)


@bot.slash_command(description="Выбор группы для просмотра расписания")
async def desc(inter: disnake.ApplicationCommandInteraction, group: str = None):
    await inter.response.defer()
    groups = await college.get_groups()
    if not group:
        view = GroupsView(list(groups), college, inter.user.id)
        await inter.followup.send(view=view)
    else:
        if group.upper() in groups:
            group_object = await college.get_desc_by_url(groups[group.upper()])
            week = group_object.get_week()
            if len(week.days) > 0:
                await inter.followup.send(
                    view=WeekdaysView(group.upper(), group_object, groups, college, inter.user.id),
                    content=f"{week.start_date.strftime('%d.%m.%Y')} – {week.end_date.strftime('%d.%m.%Y')}")
            else:
                await inter.followup.send(content="У данной группы нет пар на этой неделе!", ephemeral=True)
        else:
            await inter.followup.send("Группа не найдена!", ephemeral=True)


@bot.slash_command(description="Добавить группу в хендлер событий")
async def add_group(inter: disnake.ApplicationCommandInteraction, group: str):
    await inter.response.defer()
    groups = await college.get_groups()
    if group.upper() in groups:
        if not database.chat_is_exist(group.upper(), get_channel_or_user_id(inter)):
            await database.insert_group(group.upper(), inter.guild_id, get_channel_or_user_id(inter))
            await inter.followup.send(f"_Группа **{group.upper()}** добавлена в лист событий!_")
        else:
            await inter.followup.send(f"Группа **{group.upper()}** уже добавлена для этого канала!")
    else:
        await inter.followup.send("Группа не найдена!", ephemeral=True)


@bot.slash_command(description="Удалить группу из хендлера событий")
async def del_group(inter: disnake.ApplicationCommandInteraction, group: str):
    await inter.response.defer()
    groups = await college.get_groups()
    if group.upper() in groups:
        if database.chat_is_exist(group.upper(), get_channel_or_user_id(inter)):
            database.delete_group(group.upper(), get_channel_or_user_id(inter))
            await inter.followup.send(f"_Группа **{group.upper()}** удалена из листа событий!_")
        else:
            await inter.followup.send(f"Группа **{group.upper()}** уже удалена для этого канала!")
    else:
        await inter.followup.send("Группа не найдена!", ephemeral=True)


@bot.event
async def on_ready():
    await database.init()
    week_handler.start()
    print('[INFO] Bot connected!')


# bot.run('MTA3NzEwMjI4MDMyMDQ4NzUwNA.G1Jpqv.HBU4M7r992WWfbmiP_tYB2323M-HeCDUafXWA0')
bot.run('MTA4MDgwMDkyNzc1MTA4MjAwNA.GE2NJS.wxHlNU2A5lLJljhTchAvmk9iJJjr2egpfDuJzQ')
