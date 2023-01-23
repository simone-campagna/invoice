# -*- coding: utf-8 -*-
#
# Copyright 2015 Simone Campagna
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

__author__ = "Simone Campagna"
__all__ = [
    'Week',
    'WeekManager',
]

import collections
import datetime

Week = collections.namedtuple('Week', ('week_number', 'week_day'))

class WeekManager(object):
    def __init__(self):
        self._year_weeks = {}
        self._year_days = {}

    def year_setup(self, year):
        self._year_days[year] = []
        self._year_weeks[year] = []
        jan1 = datetime.date(year, 1, 1)
        dec31 = datetime.date(year, 12, 31)
        one_day = datetime.timedelta(days=1)
        six_days = datetime.timedelta(days=6)
        week_number = 1
        week_day = jan1.weekday()
        week_first = jan1
        week_last = week_first + one_day * (6 - week_day)
        year_weeks = self._year_weeks[year]
        year_weeks.append((week_first, week_last))
        while week_last < dec31:
            week_first = week_last + one_day
            week_last = min(week_first + six_days, dec31)
            year_weeks.append((week_first, week_last))
        year_days = self._year_days[year]
        for week_ordinal, (week_first, week_last) in enumerate(year_weeks):
            week_number = week_ordinal + 1
            d = week_first
            week_day = 0
            while d <= week_last:
                year_days.append(Week(week_number=week_number, week_day=week_day))
                week_day += 1
                d += one_day

    def get_year_weeks(self, year):
        if not year in self._year_weeks:
            self.year_setup(year)
        return self._year_weeks[year]

    def get_year_days(self, year):
        if not year in self._year_days:
            self.year_setup(year)
        return self._year_days[year]

    def week_range(self, year, week_number):
        year_weeks = self.get_year_weeks(year)
        return year_weeks[week_number - 1]

    def year_day(self, day):
        return day.timetuple().tm_yday

    def week(self, day):
        year_days = self.get_year_days(day.year)
        return year_days[self.year_day(day)]

    def week_day(self, day):
        return self.week(day).week_day

    def week_number(self, day):
        return self.week(day).week_number

