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
    'UpgraderMeta',
    'Upgrader',
    'MajorMinorUpgrader',
]

import abc
import inspect

from ...version import Version, VERSION

class UpgraderMeta(abc.ABCMeta):
    REGISTRY = []
    def __new__(mcls, class_name, class_bases, class_dict):
        cls = super().__new__(mcls, class_name, class_bases, class_dict)
        if not cls.isabstract():
            mcls.REGISTRY.append(cls())
        return cls

class Upgrader(metaclass=UpgraderMeta):
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

class MajorMinorUpgrader(Upgrader):
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

