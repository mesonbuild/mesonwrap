# Copyright 2015 The Meson development team
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

from flask import g
import os

from mesonwrap import wrapdb
from mesonwrap import wrapupdater

DB_DIRECTORY = os.path.normpath(os.path.join(os.path.split(__file__)[0], ".."))

def get_query_db():
    db = getattr(g, "_query_database", None)
    if db is None:
        db = g._query_database = wrapdb.WrapDatabase(DB_DIRECTORY)
    return db

def get_update_db():
    db = getattr(g, "_update_database", None)
    if db is None:
        db = g._update_database = wrapupdater.WrapUpdater(DB_DIRECTORY)
    return db

