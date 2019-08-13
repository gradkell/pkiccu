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


from pkiccu.http_utils import HttpUtils
from pkiccu.cert_bundler import CertBundler
from pkiccu.x509_utils import X509Utils
from pathlib import Path
from pkiccu.disa_crl_scraper import DisaCrlScraper
import tempfile
from zipfile import ZipFile, is_zipfile
import shutil
from datetime import datetime
from tqdm import tqdm
import sys
import os
import logging


class DisaDownloader:
    URL_DISA = DisaCrlScraper.URL_DISA

    CAT_ID = "id"
    CAT_ID_SW = "id_sw"
    CAT_SW = "sw"
    CAT_EMAIL = "email"
    CAT_ROOT = "root"
    CAT_ECA = "eca"
    CAT_WCF = "wcf"
    CAT_INTEROP = "interop"
    CAT_OTHER = "other"

    CATEGORIES = [CAT_ID,
                  CAT_ID_SW,
                  CAT_SW,
                  CAT_EMAIL,
                  CAT_ROOT,
                  CAT_ECA,
                  CAT_WCF,
                  CAT_INTEROP,
                  CAT_OTHER]

    def __init__(self, base_dir: str = ".", url_disa: str = URL_DISA, http_utils: HttpUtils = None):
        self.base_path = Path(base_dir)
        self.url_disa = url_disa
        self.http_utils = http_utils
        if not self.http_utils:
            self.http_utils = HttpUtils()
        self.disa_crl_scraper = DisaCrlScraper(
            url_disa=self.url_disa, http_utils=self.http_utils)
        self.__init_dirs()

    def __init_dirs(self):
        for dir in DisaDownloader.CATEGORIES:
            (self.base_path / Path(dir) / "certs").mkdir(parents=True, exist_ok=True)
            (self.base_path / Path(dir) / "crls").mkdir(parents=True, exist_ok=True)

    def name_to_category(self, ca: str) -> str:
        dir_return = DisaDownloader.CAT_OTHER

        if self.disa_crl_scraper.is_id_ca(ca):
            dir_return = DisaDownloader.CAT_ID
        elif self.disa_crl_scraper.is_id_sw_ca(ca):
            dir_return = DisaDownloader.CAT_ID_SW
        elif self.disa_crl_scraper.is_sw_ca(ca):
            dir_return = DisaDownloader.CAT_SW
        elif self.disa_crl_scraper.is_email_ca(ca):
            dir_return = DisaDownloader.CAT_EMAIL
        elif self.disa_crl_scraper.is_eca(ca):
            dir_return = DisaDownloader.CAT_ECA
        elif self.disa_crl_scraper.is_interop(ca):
            dir_return = DisaDownloader.CAT_INTEROP
        elif self.disa_crl_scraper.is_wcf(ca):
            dir_return = DisaDownloader.CAT_WCF
        elif self.disa_crl_scraper.is_dod_root_ca(ca):
            dir_return = DisaDownloader.CAT_ROOT
        else:
            # print(f"{ca} classified as {dir_return}")
            pass

        return dir_return

    def download_certs(self, noprogress: bool = None, check_hash: bool = True, check_parse: bool = True):
        ca_names = self.disa_crl_scraper.get_ca_names()
        # doing it this way makes lots of requests.
        # the other way is to use their naming convention for cert files
        if not ca_names:
            raise RuntimeError("Could not get CA names list from DISA")
        else:
            with tqdm(total=len(ca_names), desc="Downloading...", unit="Certs", disable=noprogress, smoothing=0.1) as pbar:
                for ca in ca_names:
                    try:
                        if ca and ca != "ALL CRL ZIP":
                            logging.debug(f"Downloading cert for '{ca}'...")
                            pbar.set_description(ca)
                            dl_file = self.base_path / \
                                Path(self.name_to_category(ca)) / "certs"
                            fn = dl_file / \
                                Path(self.disa_crl_scraper.name_to_filename(
                                    ca) + ".cer")
                            if fn.exists():
                                logging.debug(
                                    f"Skipping CA cert '{ca}' because file '{fn.name}' already exists.")
                            else:
                                if not self.disa_crl_scraper.is_root_ca(ca):
                                    path_cert_file = self.disa_crl_scraper.download_cert(
                                        ca=ca, filename=dl_file, progress_label=ca, noprogress=True, check_hash=check_hash)
                                    if check_parse and path_cert_file and path_cert_file.exists():
                                        try:
                                            cert = X509Utils.load_cert_der(
                                                path_cert_file)
                                            if cert == None:
                                                raise RuntimeError()
                                        except:
                                            logging.debug(
                                                f"Cert file failed parse check: {str(path_cert_file)}")
                                            try:
                                                os.remove(path_cert_file)
                                            except:
                                                pass
                                            raise RuntimeError(
                                                f"Could not parse cert file '{path_cert_file.name}'")
                    except BaseException as ex:
                        logging.exception(
                            f"Error downloading cert for CA '{ca}'")
                        print(str(ex), file=sys.stderr)
                    pbar.update(1)
                pbar.set_description("Cert Downloads Complete")

    def download_crls(self, noprogress: bool = None, check_parse: bool = True):
        ca_names = self.disa_crl_scraper.get_ca_names()
        # doing it this way makes lots of requests.
        # the other way is to use their naming convention for cert files
        with tqdm(total=len(ca_names), desc="Downloading...", unit="CRLs", disable=noprogress, smoothing=0.1) as pbar:
            for ca in ca_names:
                try:
                    if ca != "ALL CRL ZIP":
                        logging.debug(f"Downloading CRL for '{ca}'...")
                        pbar.set_description(ca)
                        dl_file = self.base_path / \
                            Path(self.name_to_category(ca)) / "crls"
                        path_crl_file = self.disa_crl_scraper.download_crl(
                            ca=ca, filename=dl_file, progress_label=ca, noprogress=True)
                        if check_parse and path_crl_file and path_crl_file.exists():
                            try:
                                pbar.set_description(
                                    f"Parsing {path_crl_file.name}")
                                crl = X509Utils.load_crl_der(
                                    path_crl_file)
                                if crl == None:
                                    raise RuntimeError()
                            except:
                                logging.debug(
                                    f"CRL file failed parse check: {str(path_crl_file)}")
                                try:
                                    os.remove(path_crl_file)
                                except:
                                    pass
                                raise RuntimeError(
                                    f"Could not parse CRL file '{path_crl_file.name}'")

                except BaseException as ex:
                    logging.exception(f"Error downloading CRL for CA '{ca}'")
                    print(str(ex), file=sys.stderr)
                pbar.update(1)
            pbar.set_description("CRL Downloads Complete")

    def download_crls_zip(self, crl_zip_archive_dir: str = None, noprogress: bool = None, check_parse: bool = True):
        dl_dir = crl_zip_archive_dir
        prefer_cd_filename = False
        tmp_dir = None

        if not dl_dir:
            tmp_dir = tempfile.mkdtemp()
            dl_dir = tmp_dir
            prefer_cd_filename = True
        else:
            dl_dir = str(Path(
                dl_dir) / Path(f"ALLCRLZIP_{datetime.now().replace(microsecond=0).isoformat()}.zip"))

            # Windows can't have colons in the time part -- invalid filename
            dl_dir = dl_dir.replace(":", "-")

            Path(dl_dir).parent.mkdir(parents=True, exist_ok=True)

        logging.debug(f"Downloading ALL CRL ZIP to '{str(dl_dir)}'...")
        path_zip = self.disa_crl_scraper.download_all_crl_zip(
            filename=dl_dir, prefer_cd_filename=prefer_cd_filename, progress_label="ALL CRL ZIP", noprogress=noprogress)

        if not is_zipfile(path_zip):
            raise RuntimeError(f"Invalid zip file: {str(path_zip)}")

        zip = ZipFile(path_zip, mode="r", allowZip64=True)

        members = zip.namelist()
        logging.debug(f"Extracting ALL CRL ZIP...")
        with tqdm(total=len(members), desc="Extracting", unit="F", disable=noprogress, smoothing=0.1) as pbar:
            for member in members:
                try:
                    pbar.set_description(
                        desc=f"Extracting {Path(str(member)).name}")
                    dir = self.base_path / \
                        Path(self.name_to_category(
                            self.disa_crl_scraper.filename_to_name(member))) / "crls"
                    crl_fn = zip.extract(member, dir)
                    path_crl_file = Path(crl_fn)
                    if check_parse and path_crl_file and path_crl_file.exists():
                        try:
                            pbar.set_description(
                                f"Parsing {path_crl_file.name}")
                            crl = X509Utils.load_crl_der(
                                path_crl_file)
                            if crl == None:
                                raise RuntimeError()
                        except:
                            logging.debug(
                                f"CRL file failed parse check: {str(path_crl_file)}")
                            try:
                                os.remove(path_crl_file)
                            except:
                                pass
                            raise RuntimeError(
                                f"Could not parse CRL file '{path_crl_file.name}'")
                except BaseException as ex:
                    logging.exception(
                        f"Error exctracting or processing {member}")
                    print(str(ex), file=sys.stderr)
                pbar.update(1)
            pbar.set_description(desc="Extraction Complete")

        if not crl_zip_archive_dir and tmp_dir:
            shutil.rmtree(tmp_dir)
