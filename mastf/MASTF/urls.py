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
from django.urls import include, path, register_converter

from mastf.MASTF import settings, converters


for name, clazz in converters.listconverters().items():
    register_converter(clazz, name)

urlpatterns = [
    path("api/v1/", include("mastf.MASTF.rest.urls")),
]

if settings.DEBUG:
    urlpatterns.extend(
        [path("api-auth/", include("rest_framework.urls", namespace="rest_framework"))]
    )

if not settings.API_ONLY:
    from mastf.MASTF.web import views

    urlpatterns.extend(
        [
            path("web/", include("mastf.MASTF.web.urls")),
            path("", views.DashboardView.as_view()),
        ]
    )
