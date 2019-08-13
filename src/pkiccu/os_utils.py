# Copyright 2019 Gradkell Systems, Inc.
# Author: Mike R. Prevost, mprevost@gradkell.com
#
# This file is part of PKICCU.
#
# PKICCU is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# PKICCU is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import platform


class OsUtils:
    def get_raw_platform():
        return platform.system()

    def get_platform_name():
        name_return: str = "unsupported"
        plat: str = platform.system().lower()
        if plat.find("windows") >= 0:
            name_return = "win"
        elif plat.find("darwin") >= 0:
            name_return = "mac"
        elif plat.find("linux") >= 0:
            name_return = "lnx"
        return name_return

    def is_win():
        return OsUtils.get_platform_name() == "win"

    def is_mac():
        return OsUtils.get_platform_name() == "mac"

    def is_lnx():
        return OsUtils.get_platform_name() == "lnx"
