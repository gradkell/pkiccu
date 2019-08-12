#! /usr/bin/env python

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

from pathlib import Path
import zipfile
import sys
import shutil
from src.pkiccu.version import VERSION
import subprocess
import platform
import os

PROG_NAME = "pkiccu"


class Build:
    def __init__(self):
        self.platform = self.get_platform_name()
        self.is_windows = (self.platform == "win")
        self.exe_ext = ".exe" if self.is_windows else ""

    def get_platform_name(self):
        name_return: str = "unsupported"
        plat: str = platform.system().lower()
        if plat.find("windows") >= 0:
            name_return = "win"
        elif plat.find("darwin") >= 0:
            name_return = "mac"
        elif plat.find("linux") >= 0:
            name_return = "lnx"
        return name_return

    def get_src_files(self, root: str = "") -> dict:
        dict_return: dict = {}
        glob = Path("src").glob("**/*.py")
        for fn in glob:
            dict_return[str(fn)] = str(Path(root) / fn)
        glob = Path("var").glob("**/*")
        for fn in glob:
            dict_return[str(fn)] = str(Path(root) / fn)
        for fn in ["README.md", "COPYING", "COPYRIGHT", "PipFile", "PipFile.lock", "build.py"]:
            dict_return[str(fn)] = str(Path(root) / fn)
        return dict_return

    def get_bin_files(self, root: str = "") -> dict:
        dict_return: dict = {}
        for fn in ["README.md", "COPYING", "COPYRIGHT"]:
            dict_return[str(fn)] = str(Path(root) / fn)
        dict_return[f"dist/pkiccu{self.exe_ext}"] = str(
            Path(root) / f"pkiccu{self.exe_ext}")
        dict_return[f"dist/run_dbsign_crl_updater{self.exe_ext}"] = str(
            Path(root) / f"scripts/run_dbsign_crl_updater{self.exe_ext}")
        dict_return["var/pkiccu.cfg"] = str(Path(root) / "pkiccu.cfg")
        dict_return["var/roots.bundle"] = str(Path(root) / "roots.bundle")
        return dict_return

    def make_zip(self, fn: str, fn_dict: dict, root: str = ""):
        with zipfile.ZipFile(fn, "w", zipfile.ZIP_DEFLATED) as zip:
            for fn in fn_dict.keys():
                zip.write(fn, Path(root) / fn_dict.get(fn))

    def run_pyinstaller(self, spec_file: str):
        subprocess.run(args=["pyinstaller",
                             "--onefile",
                             spec_file],
                       shell=False,
                       cwd=".",
                       check=True)

    def make_dist_src(self, prefix: str = f"{PROG_NAME}"):
        Path("dist").mkdir(parents=True, exist_ok=True)
        fn_dict: dict = self.get_src_files(root=f"{prefix}_src")
        self.make_zip(f"dist/{prefix}_src.zip", fn_dict)

    def make_dist_bin(self, prefix: str = f"{PROG_NAME}"):
        Path("dist").mkdir(parents=True, exist_ok=True)
        self.run_pyinstaller("var/pkiccu.spec")
        self.run_pyinstaller("var/run_dbsign_crl_updater.spec")
        fn_dict: dict = self.get_bin_files(root=f"{prefix}_{self.platform}")
        self.make_zip(f"dist/{prefix}_{self.platform}.zip", fn_dict)
        os.remove(Path(f"dist/pkiccu{self.exe_ext}"))
        os.remove(Path(f"dist/run_dbsign_crl_updater{self.exe_ext}"))

    def main(self) -> int:
        prefix: str = f"{PROG_NAME}_{VERSION}"
        self.make_dist_src(prefix)
        self.make_dist_bin(prefix)
        pass


###
# Actually call Build.main()
###
if __name__ == '__main__':
    sys.exit(Build().main())
