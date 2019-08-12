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


import argparse
import sys
from pathlib import Path
from pkiccu.version import VERSION


class ArgUtils:
    PROG_VER = VERSION
    PROD_DESC = f"""
    PKICCU (pronounced 'peek-ih-choo') is the "PKI Certificate and CRL Updater".
    PKICCU is a configurable utility that downloads PKI certifates, CRLs and other files.
    PKICCU can create openssl-style certificate bundles which are used with webservers such
    as Apache to configure SSL client-certificate validation.  PKICCU can also run user
    provided external programs when the update operations are complete.
    """

    def parse() -> dict:
        args_return = {}
        prog = Path(sys.argv[0]).name
        parser = argparse.ArgumentParser(prog=prog,
                                         description=ArgUtils.PROD_DESC)

        parser.add_argument("-c", "--config",
                            default="./pkiccu.cfg",
                            help="Config file location (defaults to './pkiccu.cfg').")
        parser.add_argument("-v", "--version",
                            action="version",
                            help="Print the version number and exit.",
                            version=ArgUtils.PROG_VER)
        parser.add_argument("--nodisacerts",
                            action="store_true",
                            help="Do not download DoD PKI CA certificates from DISA.")
        parser.add_argument("--nodisacrls",
                            action="store_true",
                            help="Do not download DoD PKI CRLs from DISA")
        parser.add_argument("--nourldownload",
                            action="store_true",
                            help="Do not download other URLs")
        parser.add_argument("--nobundles",
                            action="store_true",
                            help="Do not create cert bundles")
        parser.add_argument("--noscripts",
                            action="store_true",
                            help="Do not run scripts")
        parser.add_argument("--noprogress",
                            action="store_true",
                            help="Do not show progress bars (defaults to auto mode)")

        _args = parser.parse_args()

        if _args:
            args_return = vars(_args)

        return args_return
