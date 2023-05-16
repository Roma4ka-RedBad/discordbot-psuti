import bs4
from datetime import datetime
from loguru import logger
from typing import List
from utils import async_request, parting
from models import DescWeek, DescDay, DescLesson


class DescObject:
    def __init__(self, group_url, week_object, days_object):
        self.group_url = group_url
        self.html_week_block = week_object
        self.html_days_block = days_object
        self.trash_blocks = ['<td bgcolor="ffffff" colspan="7" height="5"></td>']
        self.color_schemes = {
            "t_c2c41d_12": 0xFF1E00,
            "классный_час": 0x585858,
            "экзамен": 0xFA034F,
            "консультация": 0x9F17A8,
            "ffffbb": 0xFFFFBB,
        }

    @staticmethod
    def _set_hyperlinks(text: str, contents: List[bs4.Tag]):
        for content in contents:
            if isinstance(content, bs4.Tag):
                if content.a:
                    text = text.replace(content.a.text, f"[{content.a.text}]({content.a.get('href')})")
        return text

    def get_lessons(self, day_blocks: list) -> List[DescLesson]:
        lessons = []
        for html_lesson in parting(day_blocks, 7):
            lesson = DescLesson()
            main_bgcolor = None
            for obj_id, obj in enumerate(html_lesson):
                try:
                    match obj_id:
                        case 0:
                            lesson.number = obj.text
                            main_bgcolor = obj.attrs['bgcolor']
                        case 1:
                            if obj.a:
                                if obj.a['class'][0] in self.color_schemes:
                                    lesson.bgcolor = self.color_schemes[obj.a['class'][0]]
                            lesson.timeline = obj.text
                        case 2:
                            lesson.process_type = obj.get_text(separator="\n")
                        case 3:
                            lesson.discipline = obj.get_text(separator="\n")
                        case 4:
                            lesson.theme = self._set_hyperlinks(obj.get_text(separator="\n"), obj.contents)
                        case 5:
                            lesson.resources = self._set_hyperlinks(obj.get_text(separator="\n"), obj.contents)
                        case 6:
                            lesson.tasks = self._set_hyperlinks(obj.get_text(separator="\n"), obj.contents)
                except Exception:
                    logger.error(f"Error in parsing college code ({obj_id})!")

            event_type = lesson.number.lower().strip().replace(" ", "_")
            if event_type in self.color_schemes:
                lesson.bgcolor = self.color_schemes[event_type]
            elif main_bgcolor in self.color_schemes:
                lesson.bgcolor = self.color_schemes[main_bgcolor]
            elif lesson.bgcolor:
                pass
            else:
                lesson.bgcolor = 0x436EFD

            lessons.append(lesson)
        return lessons

    def get_days(self) -> List[DescDay]:
        days = []
        days_objects = self.html_days_block.find_all('td')
        start_days_index = [days_objects.index(index) for index in
                            self.html_days_block.find_all('td', bgcolor="3481A6")]
        for start_index in start_days_index:
            day_blocks = []
            try:
                end_index = start_days_index[start_days_index.index(start_index) + 1] - 1
            except IndexError:
                end_index = 100000

            for index, day_block in enumerate(days_objects):
                if (start_index + 8) < index < end_index:
                    if str(day_block) not in self.trash_blocks:
                        day_blocks.append(day_block)
                elif index >= end_index:
                    break

            days.append(DescDay(
                date=datetime.strptime(days_objects[start_index].text.split()[1], '%d.%m.%Y'),
                lessons=self.get_lessons(day_blocks)
            ))
        return days

    def get_week(self) -> DescWeek:
        args = []
        for html_obj in self.html_week_block.find_all('td', align='center'):
            if 'по' in (obj := html_obj.text.split()):
                args.append(datetime.strptime(obj[1], '%d.%m.%Y'))
                args.append(datetime.strptime(obj[3], '%d.%m.%Y'))

        for html_obj in self.html_week_block.find_all('a'):
            if html_obj.get('href') and html_obj.text:
                args.append(html_obj.get('href'))

        return DescWeek(
            start_date=args[0],
            end_date=args[1],
            days=self.get_days(),
            last_week_href=args[2],
            total_week_href=self.group_url,
            next_week_href=args[3]
        )


class CollegeDesc:
    def __init__(self, url='https://lk.ks.psuti.ru/'):
        self.url = url

    async def get_groups(self) -> dict:
        page = await async_request(self.url)
        if page:
            page = bs4.BeautifulSoup(page, 'lxml')
            group_urls = {}

            html_obj = page.find_all('a')
            for a_block in html_obj:
                if 'obj' in a_block.get('href'):
                    group_urls.update({
                        a_block.b.text.upper(): a_block.get('href')
                    })

            return group_urls

    async def get_desc_by_url(self, group_url: str) -> DescObject:
        desc_object = await async_request(self.url + group_url)
        if desc_object:
            desc_object = bs4.BeautifulSoup(desc_object, 'lxml')
            tables = [obj for obj in desc_object.body if obj.name == 'table']
            return DescObject(group_url, tables[1], tables[2])
