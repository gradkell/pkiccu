# Copyright 2019 Gradkell Systems, Inc. Author: Mike R. Prevost,
# mprevost@gradkell.com
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


from typing import Dict, List
from pathlib import Path


class FileUtils:

    def read_file(fn: str, binary: bool = True):
        data_return = None
        if fn:
            mode = "rb" if binary else "r"
            with open(fn, mode) as file:
                data_return = file.read()
        return data_return

    def read_text_file(fn: str) -> str:
        return FileUtils.read_file(fn, binary=False)

    def get_matching_files(dir: str, pattern: str = r".*", recursive: bool = False) -> List:
        list_return: []
        if dir:
            path_dir = Path(dir)
            if path_dir.exists():
                if recursive and not pattern.startswith("**/"):
                    pattern = "**/" + pattern
                list_return = [str(path) for path in path_dir.glob(
                    pattern) if path.is_file()]
        return list_return
