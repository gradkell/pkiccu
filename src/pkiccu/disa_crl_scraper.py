# Copyright 2019 Gradkell Systems, Inc.
#
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


"""
The disa_crl_scraper module contains the DisaCrlScraper which contains utilities
for listing and downloading certs and CRLs from DISA
"""

#from typing import Callable
from bs4 import BeautifulSoup
from pkiccu.http_utils import HttpUtils
from pathlib import Path
import gzip
import shutil
import os
import re
import urllib
import hashlib


class DisaCrlScraper:
    """ 
    This class contains functions which scrape data from the DISA CRL website.
    """

    URL_DISA = "https://crl.gds.disa.mil"

    BS4_PARSER = "html5lib"  # html5lib is slower but more lenient than "html.parser"

    def __init__(self, url_disa: str = URL_DISA, http_utils: HttpUtils = None):
        if (http_utils):
            self.http_utils = http_utils
        else:
            self.http_utils = HttpUtils()
        self.url_disa = url_disa
        self.url_disa_details = f"{self.url_disa}/details"
        self.url_disa_dl_cert = f"{self.url_disa}/getsign"
        self.url_disa_view_cert = f"{self.url_disa}/viewsign"
        self.ca_info = {}
        self.ca_details = {}
        self.ca_filename_to_name = {}

    def get_ca_list(self) -> dict:
        """ 
        Gets the CA list by scraping DISA's website.

        Returns: dict: a dictionary of CA name => CA DN
        """
        dict_return = None

        if len(self.ca_info) > 0:
            dict_return = self.ca_info
        else:
            try:
                #print("Getting CA list... ")
                page_text = self.http_utils.doTextRequest(
                    self.url_disa, "GET")

                if page_text:
                    # print("Parsing...")
                    soup = BeautifulSoup(page_text, DisaCrlScraper.BS4_PARSER)
                    tagCaList = soup.find("select", id='CAList')
                    if tagCaList:
                        options = tagCaList.find_all('option')
                        if options:
                            self.ca_info = {option.text: option.get('value')
                                            for option in options}
                            self.ca_filename_to_name = {self.name_to_filename(
                                name): name for name in self.ca_info.keys()}

                            # TODO: DELETE ME self.ca_info.pop("DOD ID CA-50")

                            dict_return = self.ca_info
            except BaseException as e:
                dict_return = None
                raise e

        return dict_return

    def get_ca_names(self) -> list:
        list_return = None
        ca_list = self.get_ca_list()
        if ca_list:
            list_return = list(ca_list)
        return list_return

    def get_ca_view(self, ca: str) -> str:
        page_text = self.http_utils.doTextRequest(
            self.url_disa_view_cert + f"?{urllib.parse.quote_plus(ca)}", "GET")
        return page_text

    def get_sha1hash_from_ca_view(self, page_text: str) -> str:
        str_return: str = None
        match = re.search(r"\W\s*SHA-1:\s*(\w+)\s*\W",
                          page_text, re.IGNORECASE)
        if match:
            str_return = match.group(1)
            if str_return:
                str_return = str_return.upper().strip()
        return str_return

    def get_ca_details(self, ca: str) -> dict:
        """ 
        Gets the CA cert and CRL download URLs by scraping DISA's website.

        Parameters: ca (str): the DN of the CA as returned by get_ca_list()

        Returns: dict: A dictionary whose values are URLs for downloading cert
        and crls.  The keys can be cert, crl, crl_gzip, or crl_zip.  "crl_zip"
        only seems to be there for ALL CRLS ZIP.
        """
        self.get_ca_list()

        dn = self.ca_info.get(ca)
        if not dn:
            raise RuntimeError(
                f"CA name not found ({ca})")

        dict_return = self.ca_details.get(dn)

        if not dict_return:
            try:
                #print("Getting CA Details for: " + ca)

                page_text = self.http_utils.doTextRequest(
                    self.url_disa_details, "POST", data={"dn": dn})

                # print("Parsing...")
                soup = BeautifulSoup(page_text, DisaCrlScraper.BS4_PARSER)

                link_ca_cert = soup.find("a", id='dlCASign')
                link_ca_crl = soup.find("a", id='dlCACrl')
                link_ca_crl_gzip = soup.find("a", id='dlCAGZip')
                link_ca_crl_zip = soup.find("a", id='dlCAZip')

                dict_return = {}
                if link_ca_cert:
                    dict_return["cert"] = self.url_disa + \
                        "/" + link_ca_cert["href"]
                if link_ca_crl:
                    dict_return["crl"] = self.url_disa + \
                        "/" + link_ca_crl["href"]
                if link_ca_crl_gzip:
                    dict_return["crl_gzip"] = self.url_disa + \
                        "/" + link_ca_crl_gzip["href"]
                if link_ca_crl_zip:
                    dict_return["crl_zip"] = self.url_disa + \
                        "/" + link_ca_crl_zip["href"]

                view_text = self.get_ca_view(ca)
                if view_text:
                    digest_sha1 = self.get_sha1hash_from_ca_view(view_text)
                    if digest_sha1:
                        dict_return["sha1"] = digest_sha1

                self.ca_details[ca] = dict_return
            except BaseException as e:
                dict_return = None
                raise e

        return dict_return

    def get_all_ca_details(self):
        """
        """
        self.get_ca_list()

        for ca in self.ca_info.keys:
            self.get_ca_details(ca)
        return self.ca_details

    def check_file_hash_sha1(self, fn: str, hash: str) -> bool:
        bool_return: bool = False
        if fn and hash:
            with open(fn, "rb") as file:
                file_hash = hashlib.sha1(
                    file.read()).hexdigest().upper().strip()
            bool_return = file_hash == hash.upper().strip()
        return bool_return

    def download_cert(self, ca: str, filename: str, prefer_cd_filename: bool = True, progress_label: str = None, noprogress: bool = None, check_hash: bool = True) -> Path:
        """
        """
        path_return = None
        ca_details = self.get_ca_details(ca)
        url = ca_details.get('cert')
        if url:
            path_return = self.http_utils.downloadBinaryFile(
                url=url, filename=filename, method="GET", prefer_cd_filename=True, progress_label=progress_label, noprogress=noprogress)
            if check_hash and path_return and path_return.exists():
                detail_hash = ca_details.get("sha1")
                if detail_hash:
                    check_ok = self.check_file_hash_sha1(
                        path_return, detail_hash)
                    if not check_ok:
                        os.remove(path_return)
                        path_return = None
                        raise RuntimeError(
                            f"Digest from DISA website doesn't match downloaded cert file for CA '{ca}'")

        return path_return

    def download_crl(self, ca: str, filename: str, prefer_cd_filename: bool = True, progress_label: str = None, noprogress: bool = None) -> Path:
        """
        """
        path_return = None
        ca_details = self.get_ca_details(ca)

        url = ca_details.get('crl_gzip')
        if url:
            dl_path = self.http_utils.downloadBinaryFile(
                url=url, filename=filename, method="GET", prefer_cd_filename=True, progress_label=progress_label, noprogress=noprogress)

            path_return = dl_path.with_suffix("")

            with open(path_return, 'wb') as f_out, gzip.open(dl_path, 'rb') as f_in:
                shutil.copyfileobj(f_in, f_out)

            os.remove(dl_path)

        return path_return

    def download_all_crl_zip(self, filename: str, prefer_cd_filename: bool = True, progress_label: str = None, noprogress: bool = None) -> Path:
        """
        """

        ca_details = self.get_ca_details("ALL CRL ZIP")
        url = ca_details.get('crl_zip')

        # print("NOTICE: DUMMY FILE USED -- NOT REAL DOWNLOAD") if
        # url.find("nit") > 0: url =
        # "https://download.dbsign.com/tmp/updates/misc/ALLCRLZIP_JITC.zip"
        # else: url =
        # "https://download.dbsign.com/tmp/updates/misc/ALLCRLZIP_PROD.zip" url
        # = "https://httpbin.org/status/500" url =
        # "https://httpbin.org/delay/15"

        if url:
            return self.http_utils.downloadBinaryFile(
                url=url, filename=filename, method="GET", prefer_cd_filename=prefer_cd_filename, progress_label=progress_label, noprogress=noprogress)

    def is_id_ca(self, ca: str) -> bool:
        return re.search(r"ID\s+CA", ca) != None

    def is_id_sw_ca(self, ca: str) -> bool:
        return re.search(r"ID\s+SW\s+CA", ca) != None

    def is_sw_ca(self, ca: str) -> bool:
        return re.search(r"DOD\s+(JITC)*\s*SW\s+CA", ca) != None

    def is_email_ca(self, ca: str) -> bool:
        return re.search(r"EMAIL\s+CA", ca) != None

    def is_dod_root_ca(self, ca: str) -> bool:
        return re.search(r"DOD\s+(JITC)*\s*ROOT\s+CA", ca) != None

    def is_root_ca(self, ca: str) -> bool:
        return re.search(r"ROOT\s+CA", ca) != None

    def is_eca(self, ca: str) -> bool:
        return re.search(r"ECA\s+", ca) != None

    def is_wcf(self, ca: str) -> bool:
        return re.search(r"DOD\s+WCF\s+", ca) != None

    def is_interop(self, ca: str) -> bool:
        return re.search(r"INTEROPERABILITY\s+", ca) != None

    def name_to_filename(self, ca: str) -> str:
        fn_return = None
        if ca:
            fn_return = re.sub("\s+", "", ca)
            fn_return = re.sub("[-]", "_", fn_return)
        return fn_return

    def filename_to_name(self, fn: str) -> str:
        ca_return = None
        if fn:
            ca_return = self.ca_filename_to_name.get(Path(fn).stem)
        return ca_return
