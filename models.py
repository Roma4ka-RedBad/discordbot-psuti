import disnake
from utils import parting, WEEKDAYS, get_lesson_embed
from pydantic import BaseModel
from datetime import datetime
from typing import List


class DescLesson(BaseModel):
    number: str = None
    timeline: str = None
    process_type: str = None
    discipline: str = None
    theme: str = None
    resources: str = None
    tasks: str = None
    bgcolor: int = None


class DescDay(BaseModel):
    date: datetime
    lessons: List[DescLesson] = []


class DescWeek(BaseModel):
    start_date: datetime
    end_date: datetime
    days: List[DescDay]
    last_week_href: str
    total_week_href: str
    next_week_href: str


class WeekDays(disnake.ui.StringSelect):
    def __init__(self, group: str, group_data, groups_list: dict, college_url: str, user_id: int):
        self.week: DescWeek = group_data.get_week()
        self.group = group
        self.groups_list = groups_list
        self.college_url = college_url
        self.user_id = user_id
        options = [WEEKDAYS[int(day.date.strftime('%w')) - 1] for day in self.week.days]
        super().__init__(
            placeholder=f"{group} | ВЫБЕРИТЕ ДЕНЬ НЕДЕЛИ",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        if self.user_id == inter.user.id:
            embeds = []

            day = DescDay(date=datetime.now())
            for day_ in self.week.days:
                if WEEKDAYS[int(day_.date.strftime('%w')) - 1] == self.values[0]:
                    day = day_
                    break

            for lesson in day.lessons:
                embeds.append(get_lesson_embed(day, lesson, self.college_url, self.group, self.groups_list[self.group]))

            await inter.followup.edit_message(message_id=inter.message.id, embeds=embeds)
        else:
            await inter.followup.send(content="Вам не принадлежит это сообщение! Вызовите своё в этом чате или у меня в личке.", ephemeral=True)


class WeekdaysView(disnake.ui.View):
    def __init__(self, group: str, group_data, groups_list, college, user_id: int):
        super().__init__(timeout=None)
        self.group_data = group_data
        self.group = group
        self.groups_list = groups_list
        self.college = college
        self.user_id = user_id
        if len(self.group_data.get_days()) > 0:
            self.add_item(WeekDays(group, group_data, groups_list, college.url, user_id))

    @disnake.ui.button(label="предыдущая неделя", style=disnake.ButtonStyle.blurple, row=1)
    async def swap_btn_left(self, _, inter: disnake.MessageInteraction):
        await inter.response.defer()
        if self.user_id == inter.user.id:
            group_object = await self.college.get_desc_by_url(self.group_data.get_week().last_week_href)
            if group_object:
                week = group_object.get_week()
                await inter.followup.edit_message(
                    message_id=inter.message.id,
                    view=WeekdaysView(self.group.upper(), group_object, self.groups_list, self.college, self.user_id),
                    embeds=[],
                    content=f"{week.start_date.strftime('%d.%m.%Y')} – {week.end_date.strftime('%d.%m.%Y')}")
            else:
                await inter.followup.send("Произошла ошибка на сервере!", ephemeral=True)
        else:
            await inter.followup.send(content="Вам не принадлежит это сообщение! Вызовите своё в этом чате или у меня в личке.", ephemeral=True)

    @disnake.ui.button(label="выбрать группу", style=disnake.ButtonStyle.blurple, row=1)
    async def swap_change_group(self, _, inter: disnake.MessageInteraction):
        await inter.response.defer()
        if self.user_id == inter.user.id:
            view = GroupsView(list(self.groups_list), self.college, self.user_id)
            await inter.followup.edit_message(message_id=inter.message.id, view=view, embeds=[], content="")
        else:
            await inter.followup.send(content="Вам не принадлежит это сообщение! Вызовите своё в этом чате или у меня в личке.", ephemeral=True)

    @disnake.ui.button(label="следующая неделя", style=disnake.ButtonStyle.blurple, row=1)
    async def swap_btn_right(self, _, inter: disnake.MessageInteraction):
        await inter.response.defer()
        if self.user_id == inter.user.id:
            group_object = await self.college.get_desc_by_url(self.group_data.get_week().next_week_href)
            if group_object:
                week = group_object.get_week()
                await inter.followup.edit_message(
                    message_id=inter.message.id,
                    view=WeekdaysView(self.group.upper(), group_object, self.groups_list, self.college, self.user_id),
                    embeds=[],
                    content=f"{week.start_date.strftime('%d.%m.%Y')} – {week.end_date.strftime('%d.%m.%Y')}")
            else:
                await inter.followup.send("Произошла ошибка на сервере!", ephemeral=True)
        else:
            await inter.followup.send(content="Вам не принадлежит это сообщение! Вызовите своё в этом чате или у меня в личке.", ephemeral=True)


class Groups(disnake.ui.StringSelect):
    def __init__(self, group_urls: list, list_num: int, college, user_id: int):
        self.college = college
        self.user_id = user_id
        options = [disnake.SelectOption(label=group_name) for group_name in group_urls]
        super().__init__(
            placeholder=f"ВЫБЕРИТЕ ГРУППУ | ЛИСТ {list_num}",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer()
        if self.user_id == inter.user.id:
            groups_list = await self.college.get_groups()
            if groups_list:
                group_data = await self.college.get_desc_by_url(groups_list[self.values[0]])
                week = group_data.get_week()
                if len(week.days) > 0:
                    await inter.followup.edit_message(
                        message_id=inter.message.id,
                        content=f"{week.start_date.strftime('%d.%m.%Y')} – {week.end_date.strftime('%d.%m.%Y')}",
                        view=WeekdaysView(self.values[0], group_data, groups_list, self.college, self.user_id))
                else:
                    await inter.followup.send(content="У данной группы нет пар на этой неделе!", ephemeral=True)
            else:
                await inter.followup.send("Произошла ошибка на сервере!", ephemeral=True)
        else:
            await inter.followup.send(content="Вам не принадлежит это сообщение! Вызовите своё в этом чате или у меня в личке.", ephemeral=True)


class GroupsView(disnake.ui.View):
    def __init__(self, group_urls: list, college, user_id: int):
        super().__init__(timeout=None)
        multi_group_urls = parting(group_urls, 25)
        for index, group_urls in enumerate(multi_group_urls):
            self.add_item(Groups(group_urls, index + 1, college, user_id))
