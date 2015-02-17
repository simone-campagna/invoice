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
    'MetaUpgrader',
    'Upgrader',
    'Upgrader_v2_0_x__v_2_1_0',
]

import abc
import collections
import inspect

from .database.db_types import Int, Path, Bool, Str, StrTuple
from .database.db_table import DbTable

from .version import Version, VERSION

class MetaUpgrader(abc.ABCMeta):
    REGISTRY = []
    def __new__(mcls, class_name, class_bases, class_dict):
        cls = super().__new__(mcls, class_name, class_bases, class_dict)
        if not cls.isabstract():
            mcls.REGISTRY.append(cls())
        return cls

class Upgrader(metaclass=MetaUpgrader):
    @abc.abstractmethod
    def upgrade_accepts(self, version_from, version_to):
        """accepts(version_from, version_to) -> upgrade_version_to"""
        pass
    
    @abc.abstractmethod
    def downgrade_accepts(self, version_from, version_to):
        """downgrade_accepts(version_from, version_to) -> downgrade_version_to"""
        pass
    
    @classmethod
    def isabstract(cls):
        return inspect.isabstract(cls)

    def update_version(self, db, version_to, connection=None):
        with db.connect(connection) as connection:
            db.clear('version', connection=connection)
            db.write('version', [version_to], connection=connection)
        
    
    def upgrade(self, db, version_from, version_to, connection=None):
        db.logger.info("upgrade di versione da {} a {}".format(version_from, version_to))
        self.impl_upgrade(db, version_from, version_to, connection=connection)
        self.update_version(db, version_to, connection=connection)

    @abc.abstractmethod
    def impl_upgrade(db, version_from, version_to, connection=None):
        pass

    def downgrade(self, db, version_from, version_to, connection=None):
        db.logger.info("downgrade di versione da {} a {}".format(version_from, version_to))
        self.impl_downgrade(db, version_from, version_to, connection=connection)
        self.update_version(db, version_to, connection=connection)

    @abc.abstractmethod
    def impl_downgrade(db, version_from, version_to, connection=None):
        pass

    @classmethod
    def _full_upgrade_downgrade(cls, method_name, db, final_version=None):
        if method_name == 'upgrade':
            art = "l'"
            default_final_version = VERSION
            stop_condition = lambda version_from, final_version: version_from < final_version
        else:
            art = "il "
            default_final_version = Version(2, 0, 0)
            stop_condition = lambda version_from, final_version: version_from > final_version
        if final_version is None:
            final_version = default_final_version
        accepts_method_name = "{}_accepts".format(method_name)
        with db.connect() as connection:
            version_from = db.load_version(connection=connection)
            db.logger.info("full {} di versione da {} a {}".format(method_name, version_from, final_version))
            upgraders = []
            while stop_condition(version_from, final_version):
                valid_upgraders = []
                for upgrader in cls.REGISTRY:
                    accepts_method = getattr(upgrader, accepts_method_name)
                    version_to = accepts_method(version_from, final_version)
                    if version_to is not None:
                        valid_upgraders.append((version_to, upgrader))
                if valid_upgraders:
                    valid_upgraders.sort(key=lambda x: x[0], reverse=True)
                    version_to, upgrader = valid_upgraders[0]
                    upgraders.append((version_from, version_to, upgrader))
                    version_from = version_to
                else:
                    db.logger.warning("non è possibile eseguire {}{} dalla versione {} alla versione {}".format(art, method_name, version_from, final_version))
                    break
            for version_from, version_to, upgrader in upgraders:
                method = getattr(upgrader, method_name)
                method(db, version_from, version_to)

    @classmethod
    def full_upgrade(cls, db, final_version=None):
        return cls._full_upgrade_downgrade('upgrade', db=db, final_version=final_version)

    @classmethod
    def full_downgrade(cls, db, final_version=None):
        return cls._full_upgrade_downgrade('downgrade', db=db, final_version=final_version)

class Upgrader_Major_Minor(Upgrader):
    VERSION_FROM_MAJOR_MINOR = Version(None, None, None)
    VERSION_TO_MAJOR_MINOR = Version(None, None, None)
    def upgrade_accepts(self, version_from, version_to):
        if version_from[:2] == self.VERSION_FROM_MAJOR_MINOR[:2]:
            return Version(
                major=self.VERSION_TO_MAJOR_MINOR.major,
                minor=self.VERSION_TO_MAJOR_MINOR.minor,
                patch=0,
            )
        else:
            return None

    def downgrade_accepts(self, version_from, version_to):
        if version_from[:2] == self.VERSION_TO_MAJOR_MINOR[:2]:
            return Version(
                major=self.VERSION_FROM_MAJOR_MINOR.major,
                minor=self.VERSION_FROM_MAJOR_MINOR.minor,
                patch=0,
            )
        else:
            return None

class Upgrader_v2_1_x__v_2_2_0(Upgrader_Major_Minor):
    VERSION_FROM_MAJOR_MINOR = Version(2, 1, None)
    VERSION_TO_MAJOR_MINOR = Version(2, 2, 0)
    Configuration_v2_1_x = collections.namedtuple(
        'Configuration',
        ('warning_mode', 'error_mode',
         'partial_update', 'remove_orphaned',
         'header', 'total',
         'stats_group', 'list_field_names'))
    CONFIGURATION_TABLE_v2_1_x = DbTable(
        fields=(
            ('warning_mode', Str()),
            ('error_mode', Str()),
            ('remove_orphaned', Bool()),
            ('partial_update', Bool()),
            ('header', Bool()),
            ('total', Bool()),
            ('stats_group', Str()),
            ('list_field_names', StrTuple()),
        ),
        dict_type=Configuration_v2_1_x,
    )
    Configuration_v2_2_0 = collections.namedtuple(
        'Configuration',
        ('warning_mode', 'error_mode',
         'partial_update', 'remove_orphaned',
         'header', 'total',
         'stats_group', 'list_field_names',
         'show_scan_report'))
    CONFIGURATION_TABLE_v2_2_0 = DbTable(
        fields=(
            ('warning_mode', Str()),
            ('error_mode', Str()),
            ('remove_orphaned', Bool()),
            ('partial_update', Bool()),
            ('header', Bool()),
            ('total', Bool()),
            ('stats_group', Str()),
            ('list_field_names', StrTuple()),
            ('show_scan_report', Bool()),
        ),
        dict_type=Configuration_v2_1_x,
    )
    def impl_downgrade(self, db, version_from, version_to, connection=None):
        with db.connect(connection) as connection:
            cursor = connection.cursor()
            sql = """SELECT * FROM configuration;"""
            v_list = list(db.execute(cursor, sql))
            db.drop('configuration', connection=connection)
            db.create_table('configuration', self.CONFIGURATION_TABLE_v2_1_x.fields, connection=connection)
            field_names = self.Configuration_v2_1_x._fields
            sql = """INSERT INTO configuration ({field_names}) VALUES ({placeholders});""".format(
                field_names=', '.join(field_names),
                placeholders=', '.join('?' for field in field_names),
            )
            for v in v_list:
                db.execute(cursor, sql, v[:-1])
        
    def impl_upgrade(self, db, version_from, version_to, connection=None):
        with db.connect(connection) as connection:
            cursor = connection.cursor()
            sql = """SELECT * FROM configuration;"""
            values = list(db.execute(cursor, sql))[-1]
            db.drop('configuration', connection=connection)
            db.create_table('configuration', self.CONFIGURATION_TABLE_v2_2_0.fields, connection=connection)
            values +=  (False, )
            field_names = self.Configuration_v2_2_0._fields
            sql = """INSERT INTO configuration ({field_names}) VALUES ({placeholders});""".format(
                field_names=', '.join(field_names),
                placeholders=', '.join('?' for field in field_names),
            )
            db.execute(cursor, sql, values)

class Upgrader_v2_0_x__v_2_1_0(Upgrader_Major_Minor):
    VERSION_FROM_MAJOR_MINOR = Version(2, 0, None)
    VERSION_TO_MAJOR_MINOR = Version(2, 1, 0)
    Pattern_v2_0_x = collections.namedtuple('Pattern_v2_0_x', ('pattern', 'skip'))
    PATTERNS_TABLE_v2_0_x = DbTable(
        fields=(
            ('pattern', Path('UNIQUE')),
        ),
        dict_type=Pattern_v2_0_x,
    )
    Pattern_v2_1_0 = collections.namedtuple('Pattern_v2_1_x', ('pattern', ))
    PATTERNS_TABLE_v2_1_0 = DbTable(
        fields=(
            ('pattern', Path('UNIQUE')),
            ('skip', Bool()),
        ),
        dict_type=Pattern_v2_1_0,
    )

    def impl_downgrade(self, db, version_from, version_to, connection=None):
        with db.connect(connection) as connection:
            sql = """SELECT pattern, skip FROM patterns;"""
            p_list = []
            cursor = connection.cursor()
            for pattern, skip in db.execute(cursor, sql):
                p_list.append((Path.db_from(pattern), Bool.db_from(skip)))
            db.drop('patterns', connection=connection)
            db.create_table('patterns', self.PATTERNS_TABLE_v2_0_x.fields, connection=connection)
            sql = """INSERT INTO patterns (pattern) VALUES (?);"""
            for pattern, skip in p_list:
                if not skip:
                    values = (Path.db_to(pattern), )
                    db.execute(cursor, sql, values)
        
    def impl_upgrade(self, db, version_from, version_to, connection=None):
        with db.connect(connection) as connection:
            cursor = connection.cursor()
            sql = """SELECT pattern FROM patterns;"""
            p_list = []
            for pattern, in db.execute(cursor, sql):
                p_list.append(Path.db_from(pattern))
            db.drop('patterns', connection=connection)
            db.create_table('patterns', self.PATTERNS_TABLE_v2_1_0.fields, connection=connection)
            values = []
            for p in p_list:
                values.append((Path.db_to(p), Bool.db_to(False)))
            sql = """INSERT INTO patterns (pattern, skip) VALUES (?, ?);"""
            db.execute(cursor, sql, *values)


class Upgrader_Patch(Upgrader):
    def upgrade_accepts(self, version_from, version_to):
        if version_from[:2] == version_to[:2]:
            return version_to
        else:
            return None

    def downgrade_accepts(self, version_from, version_to):
        return self.upgrade_accepts(version_from, version_to)

    def impl_downgrade(self, db, version_from, version_to, connection=None):
        pass

    def impl_upgrade(self, db, version_from, version_to, connection=None):
        pass
