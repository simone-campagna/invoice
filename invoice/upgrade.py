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

from .database.db_types import Int, Path, Bool
from .database.db_table import DbTable

from .version import Version, VERSION

class MetaUpgrader(abc.ABCMeta):
    REGISTRY = []
    def __new__(mcls, class_name, class_bases, class_dict):
        cls = super().__new__(mcls, class_name, class_bases, class_dict)
        if not cls.isabstract():
            mcls.REGISTRY.append(cls)
        return cls

class Upgrader(metaclass=MetaUpgrader):
    VERSION_FROM = None
    VERSION_TO = None

    @classmethod
    def upgrade_version_from(cls):
        return cls.VERSION_FROM
    
    @classmethod
    def upgrade_version_to(cls):
        return cls.VERSION_TO
    
    @classmethod
    def downgrade_version_from(cls):
        return cls.VERSION_TO
    
    @classmethod
    def downgrade_version_to(cls):
        return cls._replace_None(cls.VERSION_FROM, 0)
    
    @classmethod
    def _replace_None(cls, version, default=0):
        l = []
        for v in version:
            if v is None:
                l.append(default)
            else:
                l.append(v)
        return Version(*l)

    @classmethod
    def isabstract(cls):
        return inspect.isabstract(cls)
    
    @classmethod
    def matches(cls, version):
        for vf, vt in zip(cls.upgrade_version_from(), version):
            if vf is not None and vf != vt:
                return False
        return True

    @classmethod
    def upgrade(cls, db, connection=None):
        cls.impl_upgrade(db, connection=connection)
        cls.update_version(db, connection=connection)

    @classmethod
    def downgrade(cls, db, connection=None):
        """only for testing"""
        cls.impl_downgrade(db, connection=connection)
        cls.update_version(db, version_to=cls.downgrade_version_to(), connection=connection)

    @classmethod
    def update_version(cls, db, version_to=None, connection=None):
        if version_to is None:
            version_to = cls.upgrade_version_to()
        with db.connect(connection) as connection:
            db.clear('version', connection=connection)
            db.write('version', [version_to], connection=connection)
        
    @abc.abstractmethod
    def impl_upgrade(db, connection=None):
        pass

    @abc.abstractmethod
    def impl_downgrade(db, connection=None):
        pass

    @classmethod
    def full_upgrade(cls, db):
        with db.connect() as connection:
            version_from = db.load_version(connection=connection)
            version_to = VERSION
            upgraders = []
            while not db.version_is_valid(version_from):
                valid_upgraders = []
                for upgrader in cls.REGISTRY:
                    if upgrader.matches(version_from):
                        distance = version_to - upgrader.upgrade_version_to()
                        valid_upgraders.append((distance, upgrader))
                if valid_upgraders:
                    valid_upgraders.sort(key=lambda x: x[0], reverse=True)
                    distance, upgrader = valid_upgraders[0]
                    upgraders.append((version_from, upgrader))
                    version_from = upgrader.upgrade_version_to()
                else:
                    db.logger.warning("non è possibile eseguire l'upgrade dalla versione {} alla versione {}".format(version_from, version_to))
                    break
            for version_from, upgrader in upgraders:
                db.logger.info("aggornamento di versione {} -> {}".format(version_from, upgrader.upgrade_version_to()))
                upgrader().upgrade(db)
        if db.version_is_valid(version_from):
            db.logger.info("aggornamento di versione {} -> {}".format(version_from, version_to))
            cls.update_version(version_to)

class Upgrader_v2_0_x__v_2_1_0(Upgrader):
    VERSION_FROM = Version(2, 0, None)
    VERSION_TO = Version(2, 1, 0)
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

    @classmethod
    def impl_downgrade(cls, db, connection=None):
        with db.connect(connection) as connection:
            sql = """SELECT pattern, skip FROM patterns;"""
            p_list = []
            cursor = connection.cursor()
            for pattern, skip in db.execute(cursor, sql):
                p_list.append((Path.db_from(pattern), Bool.db_from(skip)))
            db.drop('patterns', connection=connection)
            db.create_table('patterns', cls.PATTERNS_TABLE_v2_0_x.fields, connection=connection)
            values = []
            for pattern, skip in p_list:
                if not skip:
                    values.append((Path.db_to(pattern), ))
            sql = """INSERT INTO patterns (pattern) VALUES (?);"""
            db.execute(cursor, sql, *values)
        
    @classmethod
    def impl_upgrade(cls, db, connection=None):
        with db.connect(connection) as connection:
            sql = """SELECT pattern FROM patterns;"""
            p_list = []
            cursor = connection.cursor()
            for pattern, in db.execute(cursor, sql):
                p_list.append(Path.db_from(pattern))
            db.drop('patterns', connection=connection)
            db.create_table('patterns', cls.PATTERNS_TABLE_v2_1_0.fields, connection=connection)
            values = []
            for p in p_list:
                values.append((Path.db_to(p), Bool.db_to(False)))
            sql = """INSERT INTO patterns (pattern, skip) VALUES (?, ?);"""
            db.execute(cursor, sql, *values)

