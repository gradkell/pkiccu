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
from pkiccu.file_utils import FileUtils
from pkiccu.x509_utils import X509Utils
import sys


class CertBundler:

    def create_bundle_list(src_list: list, match: str = r"*.cer", recursive: bool = False, sort_within_dirs: bool = True, sort_all: bool = False) -> list:
        list_return = []
        if src_list:
            for src in src_list:
                try:
                    if src:
                        path_src = Path(src)
                        if path_src.exists():
                            if path_src.is_dir():
                                list_dir = FileUtils.get_matching_files(
                                    path_src, match, recursive=recursive)
                                if sort_within_dirs:
                                    list_dir = sorted(list_dir)
                                list_return = list_return + list_dir
                            else:
                                list_return.append(str(path_src))
                except BaseException as e:
                    print(str(e), file=sys.stderr)
        return list_return if not sort_all else sorted(list_return)

    def write_bundle_from_list(fn_bundle: str, fn_list: list):
        if fn_bundle and fn_list:
            with open(fn_bundle, "w") as file_bundle:
                for fn in fn_list:
                    try:
                        pem_str = X509Utils.read_der_cert_pem(fn)
                        if pem_str:
                            file_bundle.write(pem_str)
                    except BaseException as e:
                        print(str(e), file=sys.stderr)

    def write_bundle(fn_bundle: str, src_list: list, match: str = r"*.cer", recursive: bool = False, sort_within_dirs: bool = True, sort_all: bool = False):
        if fn_bundle and src_list:
            bundle_list = CertBundler.create_bundle_list(
                src_list=src_list, match=match, recursive=recursive, sort_within_dirs=sort_within_dirs, sort_all=sort_all)
            if bundle_list:
                CertBundler.write_bundle_from_list(fn_bundle, bundle_list)
