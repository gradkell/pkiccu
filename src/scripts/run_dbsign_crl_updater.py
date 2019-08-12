#! /usr/bin/env python

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

from pathlib import Path
import argparse
import subprocess
import sys


class RunDBsignCrlUpdater:
    def __init__(self):
        self.args = {}
        pass

    def parse_args(self) -> dict:
        args_return = {}
        prog = Path(sys.argv[0]).name
        parser = argparse.ArgumentParser(prog=prog,
                                         description="Script that runs the DBsign CRL Updater")

        parser.add_argument("--java",
                            required=True,
                            help="Java executable")

        parser.add_argument("--jar",
                            required=True,
                            help="DBsign CRL Updater JAR File")

        parser.add_argument("--config",
                            required=True,
                            help="DBsign CRL Updater Config File")

        parser.add_argument("--cert_dir",
                            required=False,
                            help="directory containing DER certificates to import")

        parser.add_argument("--cert_ext",
                            default="cer",
                            help="File extenstion for certificates (defaults to 'cer')")

        parser.add_argument("--cert_dir_recurse",
                            action="store_true",
                            help="Look for certificates in subdirectory tree")

        parser.add_argument("--cert_instances",
                            default="default",
                            help="Comma separated list of instances for cert import")

        parser.add_argument("--cert_delim",
                            default=",",
                            help="List delimiter for cert instance names (defaults to ',')")

        parser.add_argument("--crl_dir",
                            required=False,
                            help="directory containing DER CRLs to import")

        parser.add_argument("--crl_ext",
                            default="crl",
                            help="File extenstion for CRLs (defaults to 'crl')")

        parser.add_argument("--crl_dir_recurse",
                            action="store_true",
                            help="Look for CRLs in subdirectory tree")

        parser.add_argument("--crl_instances",
                            default="default",
                            help="Comma separated list of instances for crl import")

        parser.add_argument("--server_url",
                            required=False,
                            help="Comma separated list of server URL(s) for CRL import")

        parser.add_argument("--crl_delim",
                            default=",",
                            help="List delimiter for CRL instance names and server URLs (defaults to ',')")

        parser.add_argument("--parse",
                            action="store_true",
                            help="Parse certs/CRLs")

        _args = parser.parse_args()

        if _args:
            args_return = vars(_args)

        return args_return

    def run_crl_updater(self, java: str, jar: str, config: str, args: list) -> int:
        exit_status_return: int = 0
        try:
            cmd_line = [java, "-jar", jar, f"--configFile={config}", *args]
            print(
                f">>> Running DBsign CRL Updater, command line: {' '.join(cmd_line)}")
            completed = subprocess.run(args=cmd_line,
                                       stdout=sys.stdout,
                                       stderr=sys.stderr)
            exit_status_return = completed.returncode
        except BaseException as e:
            print(f"Error running DBsign CRL Updater: {str(e)}")
            exit_status_return = 1
        return exit_status_return

    def import_certs(self) -> int:
        exit_status_return: int = 0
        args: list = []
        args.append(f"--instances={self.args.get('cert_instances')}")
        args.append(f"--delim={self.args.get('cert_delim')}")
        args.append(f"--certFile={self.args.get('cert_dir')}")
        args.append(f"--fileExt={self.args.get('cert_ext')}")
        if (self.args.get('cert_dir_recurse') == True):
            args.append("--recurse")
        if (self.args.get('parse') == True):
            args.append("--parse")
        print("###")
        print("### IMPORTING CERTS...")
        print("###")
        exit_status_return = self.run_crl_updater(java=self.args.get("java"),
                                                  jar=self.args.get("jar"),
                                                  config=self.args.get(
                                                      "config"),
                                                  args=args)
        return exit_status_return

    def import_crls(self) -> int:
        exit_status_return: int = 0
        args: list = []
        args.append(f"--instances={self.args.get('cert_instances')}")
        args.append(f"--delim={self.args.get('crl_delim')}")
        args.append(f"--crlFile={self.args.get('crl_dir')}")
        args.append(f"--fileExt={self.args.get('crl_ext')}")
        args.append(f"--recurse={str(self.args.get('crl_dir_recurse'))}")
        if (self.args.get('crl_dir_recurse') == True):
            args.append("--recurse")
        if (self.args.get('parse') == True):
            args.append("--parse")
        print("###")
        print("### IMPORTING CRLs...")
        print("###")
        exit_status_return = self.run_crl_updater(java=self.args.get("java"),
                                                  jar=self.args.get("jar"),
                                                  config=self.args.get(
                                                      "config"),
                                                  args=args)
        return exit_status_return

    def main(self):
        exit_status_return: int = 0
        self.args = self.parse_args()
        print(self.args)
        exit_status_certs: int = 0
        exit_status_crls: int = 0
        if self.args.get('cert_dir'):
            exit_status_certs = self.import_certs()
        if self.args.get('crl_dir'):
            exit_status_crls = self.import_crls()

        if exit_status_crls == 0:
            exit_status_crls = exit_status_certs

        exit_status_return = exit_status_crls

        return exit_status_return


runner = RunDBsignCrlUpdater()
sys.exit(runner.main())
