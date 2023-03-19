from models import GroupDB
from box import Box


class Database:
    def __init__(self, college, database):
        database.create_tables([GroupDB], safe=True)
        self.groups_by_handlers = Box()
        self.college = college

    async def init(self):
        for group in GroupDB.select():
            await self.insert_group(group.group_name, group.guild_id, group.channel_id, insert_to_database=False)

    def chat_is_exist(self, group_name: str, channel_id: int):
        if group_name in self.groups_by_handlers:
            for chat in self.groups_by_handlers[group_name].chats:
                if chat.channel_id == channel_id:
                    return True

    async def insert_group(self, group_name: str, guild_id: int, channel_id: int, insert_to_database: bool = True):
        group_obj = Box(guild_id=guild_id, channel_id=channel_id)
        site_groups = await self.college.get_groups()
        if group_name in self.groups_by_handlers:
            self.groups_by_handlers[group_name]['chats'].append(group_obj)
        else:
            total_week = (await self.college.get_desc_by_url(site_groups[group_name])).get_week()
            self.groups_by_handlers[group_name] = Box(
                chats=[group_obj],
                total_week_obj=total_week,
                next_week_obj=(await self.college.get_desc_by_url(total_week.next_week_href)).get_week()
            )

        if insert_to_database:
            GroupDB.create(group_name=group_name, guild_id=guild_id, channel_id=channel_id)

        print(f"[DB] Добавлено в лист событий {group_name} ({guild_id}, {channel_id})")

    def delete_group(self, group_name: str, channel_id: int, delete_to_database: bool = True):
        for chat in self.groups_by_handlers[group_name].chats:
            if chat.channel_id == channel_id:
                print(f"[DB] Удалено из листа событий {group_name} ({chat.guild_id}, {chat.channel_id})")
                if delete_to_database:
                    group = GroupDB.get(group_name=group_name, guild_id=chat.guild_id, channel_id=chat.channel_id)
                    GroupDB.delete_by_id(group.id)

                self.groups_by_handlers[group_name].chats.remove(chat)

        if len(self.groups_by_handlers[group_name].chats) == 0:
            self.groups_by_handlers.pop(group_name)
