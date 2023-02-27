import disnake
from box import BoxList, Box
from disnake.ext import commands, tasks
from models import GroupsView, WeekdaysView
from utils import get_day_by_date, get_lesson_by_index, get_lesson_embed, get_channel_or_user_id
from college import CollegeDesc

bot = commands.Bot(command_prefix='/', intents=disnake.Intents.all(), reload=True)
college = CollegeDesc()
group_handler = BoxList()


@bot.event
async def on_ready():
    print('[INFO] Bot connected!')


@tasks.loop(seconds=10)
async def next_total_week_handler():
    for group in group_handler:

        if group.guild_id:
            channel = bot.get_guild(group.guild_id).get_channel(group.channel_id)
        else:
            channel = bot.get_user(group.channel_id)

        next_total_week_obj = await college.get_desc_by_url(group.next_total_week.total_week_href)
        next_total_week = next_total_week_obj.get_week()
        if next_total_week != group.next_total_week:
            print("Новые изменения в next week!")
            if group.next_total_week.start_date == next_total_week.start_date:
                for day in next_total_week.days:
                    founded_day = get_day_by_date(day.date, group.next_total_week.days)
                    if day != founded_day:
                        for index, lesson in enumerate(day.lessons):
                            if lesson != get_lesson_by_index(index, founded_day.lessons):
                                cvh = get_lesson_embed(day, lesson, college.url, group.group_name, group.next_total_week.total_week_href)
                                await channel.send(content="_Заметил изменения в паре на следующей неделе!_", embed=cvh)

            group.next_total_week = next_total_week


@tasks.loop(seconds=10)
async def total_week_handler():
    for group in group_handler:

        if group.guild_id:
            channel = bot.get_guild(group.guild_id).get_channel(group.channel_id)
        else:
            channel = bot.get_user(group.channel_id)

        total_week_obj = await college.get_desc_by_url(group.total_week.total_week_href)
        total_week = total_week_obj.get_week()
        if total_week != group.total_week:
            print("Новые изменения в total week!")
            if group.total_week.start_date != total_week.start_date:
                await channel.send(content="_Новая неделя наступила! Ложимся спать, завтра в садик!_")
            else:
                for day in total_week.days:
                    founded_day = get_day_by_date(day.date, group.total_week.days)
                    if day != founded_day:
                        for index, lesson in enumerate(day.lessons):
                            if lesson != get_lesson_by_index(index, founded_day.lessons):
                                cvh = get_lesson_embed(day, lesson, college.url, group.group_name, group.total_week.total_week_href)
                                await channel.send(content="_Заметил изменения в паре на этой неделе!_", embed=cvh)

            group.total_week = total_week


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
                await inter.followup.send(view=WeekdaysView(group.upper(), group_object, groups, college, inter.user.id),
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
        if True not in [group__.group_name == group.upper() and group__.channel_id == get_channel_or_user_id(inter) for group__ in group_handler]:
            group_ = Box()
            total_week_obj = await college.get_desc_by_url(groups[group.upper()])
            group_.channel_id = get_channel_or_user_id(inter)
            group_.guild_id = inter.guild_id
            group_.group_name = group.upper()
            group_.total_week = total_week_obj.get_week()
            next_total_week_obj = await college.get_desc_by_url(group_.total_week.next_week_href)
            group_.next_total_week = next_total_week_obj.get_week()
            group_handler.append(group_)
            await inter.followup.send(f"_Группа **{group.upper()}** добавлена в лист событий!_")
        else:
            await inter.followup.send(f"Группа **{group.upper()}** уже добавлена для этого канала!")
    else:
        await inter.followup.send("Группа не найдена!", ephemeral=True)


total_week_handler.start()
#next_total_week_handler.start()
bot.run('MTA3NzEwMjI4MDMyMDQ4NzUwNA.G1Jpqv.HBU4M7r992WWfbmiP_tYB2323M-HeCDUafXWA0')
