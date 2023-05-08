# This file is part of MAST-F's Frontend API
# Copyright (C) 2023  MatrixEditor, Janbehere1
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os

from whitenoise import WhiteNoise
from django.core.wsgi import get_wsgi_application

from mastf.MASTF import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mastf.MASTF.settings")

static = os.path.join(settings.BASE_DIR, "static")
application = WhiteNoise(get_wsgi_application(), root=static, prefix="static/")
