# Copyright (C) 2023 - Neil Crum (nhc.crum@outlook.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
import os

SECRET_KEY = os.environ.get('SECRET_KEY')

SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = False

CACHE_TYPE = "FileSystemCache"
DAILY_LIMIT = 1000
HOURLY_LIMIT = 240

PROCESSED_FILES_DIRECTORY = "temp/complete"