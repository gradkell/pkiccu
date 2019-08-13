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
from pkiccu.arg_utils import ArgUtils
from pkiccu.config_utils import ConfigUtils
from pkiccu.http_utils import HttpUtils
from pkiccu.disa_downloader import DisaDownloader
from pkiccu.url_downloader import UrlDownloader
from pkiccu.cert_bundler import CertBundler
from pkiccu.script_runner import ScriptRunner
from pkiccu.os_utils import OsUtils
import tempfile
import certifi
import os
from datetime import datetime
import logging
import sys


class Main:
    def __init__(self):
        self.args = None
        self.config = None
        self.temp_ca_file = None
        self.http_utils = None

    def main(self) -> int:
        exist_status_return: int = 0
        self.init()
        try:

            logging.info(f"Starting...")

            http_config = self.get_param(self.config, "http", {})
            retries = self.get_param(http_config, "retries", 5)
            timeout = self.get_param(http_config, "timeout", 5)
            chunk_size = self.get_param(http_config, "chunk_size", 1024)
            check_file_size = self.get_param(
                http_config, "check_file_size", True)
            ssl_cert_verify = self.get_param(
                http_config, "ssl_cert_verify", True)
            append_system_roots = self.get_param(
                http_config, "append_system_roots", True)

            # Possibly make a temp file containing CA certs to use in
            # ssl server cert verification
            use_ca_file = False
            if isinstance(ssl_cert_verify, str):
                if not Path(ssl_cert_verify).exists():
                    raise RuntimeError(
                        f"The specified CA bundle file for SSL server verification"
                        f"does not exist: {ssl_cert_verify}")
                else:
                    with tempfile.NamedTemporaryFile(mode="w",
                                                     suffix=".bundle",
                                                     prefix="ca_certs_",
                                                     delete=False) as ca_file:
                        self.temp_ca_file = ca_file.name
                        use_ca_file = True
                        with open(ssl_cert_verify) as roots_file:
                            ca_file.write(roots_file.read())
                            ca_file.write("\n")
                        if append_system_roots:
                            with open(certifi.where()) as certifi_file:
                                ca_file.write(certifi_file.read())

            self.http_utils = HttpUtils(retries=retries,
                                        timeout=timeout,
                                        chunk_size=chunk_size,
                                        check_file_size=check_file_size,
                                        ssl_cert_verify=(ssl_cert_verify
                                                         if not use_ca_file
                                                         else self.temp_ca_file))

            self.download_disa()

            url_download = not self.args.get("nourldownload", False)
            if url_download:
                self.url_download()

            make_bundles = not self.args.get("nobundles", False)
            if make_bundles:
                self.make_bundles()

            run_scripts = not self.args.get("noscripts", False)
            if run_scripts:
                self.run_scripts()

            if self.noprogress() != True:
                print("\nDone.\n")

            logging.info(f"Done...")

        except BaseException as e:
            logging.exception(f"An error occurred.: {str(e)}")
            print(str(e))
            exist_status_return = 1
        finally:
            if self.temp_ca_file and Path(self.temp_ca_file).exists():
                try:
                    os.remove(self.temp_ca_file)
                except:
                    pass
        return exist_status_return

    def init(self):
        self.args = ArgUtils.parse()
        config_fn = self.args.get('config')
        if not config_fn:
            raise RuntimeError("Config file name could not be determined.")
        config_path = Path(config_fn)
        if not config_path.exists():
            raise RuntimeError(
                f"Config file '{config_fn}' does not exist.")
        self.config = ConfigUtils.load(self.args.get('config'))
        self.config_logging()
        self.temp_ca_file = None
        self.http_utils = None

    def config_logging(self):
        try:
            ts_start = self.get_param(
                self.config, 'variables._ts_start', datetime.now().replace(microsecond=0).isoformat())
            filename = f"PKICCU_{ts_start}.log"
            if OsUtils.is_win():
                filename = filename.replace(":", "-")
            logging_config = self.get_param(self.config, "logging", {
                "level": "INFO",
                "filename": filename,
                "filemode": "w",
                "format": "%(asctime)s;%(levelname)s;%(message)s"
            })
            filename = self.get_param(logging_config, "filename")
            if OsUtils.is_win():
                filename = filename.replace(":", "-")
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            logging.basicConfig(level=logging.getLevelName(self.get_param(logging_config, "level")),
                                filename=filename,
                                filemode=self.get_param(
                                    logging_config, "filemode"),
                                format=self.get_param(logging_config, "format"))
        except:
            print("Cannot initialize logging system.")

    def get_param(self, config: dict, param: str, default: any = None) -> any:
        return ConfigUtils.get(config, param, default)

    def url_download(self):
        try:
            url_download = self.get_param(
                self.config, "url_downloader.url_download", True)
            if url_download:
                downloads = self.get_param(
                    self.config, "url_downloader.downloads")
                if downloads:
                    url_downloader = UrlDownloader(http_utils=self.http_utils)
                    if self.noprogress() != True:
                        print("\nDOWNLOADING OTHER FILES...\n")
                    logging.info("DOWNLOADING OTHER FILES...")
                    url_downloader.download_files(
                        downloads, noprogress=self.noprogress())
        except BaseException as e:
            logging.exception(f"Error occurred during URL download: {str(e)}")
            print(str(e))

    def download_disa(self):
        envs = self.get_param(self.config, "disa_downloader", {})
        for env_name in envs.keys():
            try:
                env = envs.get(env_name)
                data_dir = self.get_param(env, "data_dir", None)
                disa_url = self.get_param(
                    env, "disa_url", DisaDownloader.URL_DISA)
                download_certs = not self.args.get("nodisacerts", False)
                if download_certs:
                    check_cert_hashes = self.get_param(
                        env, "check_cert_hashes", True)
                    check_cert_parse = self.get_param(
                        env, "check_cert_parse", True)
                    check_crl_parse = self.get_param(
                        env, "check_crl_parse", True)
                    download_certs = self.get_param(
                        env, "download_certs", True)
                download_crls = not self.args.get("nodisacrls", False)
                if download_crls:
                    download_crls = self.get_param(env, "download_crls", True)
                    use_all_crl_zip = self.get_param(
                        env, "use_all_crl_zip", True)
                    archive_crl_zips = self.get_param(
                        env, "archive_crl_zips", True)
                    crl_zip_archive_dir = None
                    if archive_crl_zips:
                        crl_zip_archive_dir = self.get_param(
                            env, "crl_zip_archive_dir", f'{data_dir}/crl_zips')

                if data_dir:
                    downloader = DisaDownloader(
                        base_dir=data_dir, url_disa=disa_url, http_utils=self.http_utils)

                    if download_certs:
                        if self.noprogress() != True:
                            print(
                                f"\nDOWNLOADING DOD CERTS ({env_name.upper()})...\n")
                        logging.info(
                            f"DOWNLOADING DOD CERTS ({env_name.upper()})...")
                        downloader.download_certs(
                            noprogress=self.noprogress(), check_hash=check_cert_hashes, check_parse=check_cert_parse)

                    if download_crls:
                        if self.noprogress() != True:
                            print(
                                f"\nDOWNLOADING DOD CRLS ({env_name.upper()})...\n")
                        logging.info(
                            f"DOWNLOADING DOD CRLS ({env_name.upper()})...")
                        if use_all_crl_zip:
                            downloader.download_crls_zip(
                                crl_zip_archive_dir=crl_zip_archive_dir, noprogress=self.noprogress(), check_parse=check_crl_parse)
                        else:
                            downloader.download_crls(
                                noprogress=self.noprogress(), check_parse=check_crl_parse)
            except BaseException as e:
                logging.exception(
                    f"Error downloading DoD info ({env_name.upper()}): : {str(e)}")
                print(str(e))

    def make_bundles(self):
        try:
            cert_bundler = self.get_param(self.config, "cert_bundler", {})
            make_bundles = self.get_param(cert_bundler, "make_bundles", False)
            if (make_bundles):
                bundles = self.get_param(
                    cert_bundler, "bundles", None)
                if (isinstance(bundles, dict)):
                    if self.noprogress() != True:
                        print("\nMAKING CERT BUNDLES...\n")
                    logging.info(
                        f"MAKING CERT BUNDLES...")
                    for bundle_name in bundles.keys():
                        try:
                            logging.info(
                                f"Making cert bundle: '{bundle_name}'")
                            bundle = bundles.get(bundle_name)
                            if self.noprogress() != True:
                                print(f"  {bundle_name}")
                            filename = self.get_param(
                                bundle, "filename", None)
                            recursive = self.get_param(
                                bundle, "recursive", False)
                            sources = self.get_param(
                                bundle, "sources", None)
                            if isinstance(filename, str) and isinstance(sources, list):
                                match = self.get_param(
                                    bundle, "match", r"*.cer")
                                Path(filename).parent.mkdir(
                                    parents=True, exist_ok=True)
                                CertBundler.write_bundle(fn_bundle=filename,
                                                         src_list=sources, match=match, recursive=recursive)
                        except BaseException as ex:
                            logging.exception(
                                f"Error making bundle '{bundle_name}': {str(ex)}")
        except BaseException as e:
            logging.exception(f"Error making bundles: {str(e)}")
            print(str(e))

    def run_scripts(self):
        try:
            script_runner = self.get_param(self.config, "script_runner", {})
            run_scripts = self.get_param(script_runner, "run_scripts", False)
            if run_scripts:
                run_list = self.get_param(script_runner, "run_list", None)
                if run_list and isinstance(run_list, list):
                    if self.noprogress() != True:
                        print("\nRUNNING USER SCRIPTS...\n")
                    ScriptRunner.run_scripts(run_list)
        except BaseException as e:
            logging.exception(f"Error running scripts: {str(e)}")
            print(str(e))

    def noprogress(self) -> bool:
        # noprogress == None tells progress bars to only display if on a TTY.
        # Lets not interfere with this, but also have the ability to turn it off
        bool_return = self.get_param("noprogress", None)
        if self.args.get("noprogress", False) == True:
            bool_return = True
        return bool_return


###
# Actually call Main.go()
###
if __name__ == '__main__':
    sys.exit(Main().main())
