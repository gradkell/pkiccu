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
This module includes a class containing some utility functions for HTTP
"""

from typing import Dict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import urllib3
import re
from pathlib import Path
from tqdm import tqdm
import time
import os
import logging


class HttpUtils:
    def __init__(self,
                 retries: int = 3,
                 timeout: int = 10,
                 chunk_size: int = 1024,
                 check_file_size: bool = True,
                 ssl_cert_verify: bool = True):
        self.retries = retries
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.check_file_size = check_file_size

        # Start with a plain old session
        self.session = requests.session()

        self.session.verify = ssl_cert_verify
        if not ssl_cert_verify:
            urllib3.disable_warnings()
            self.session.verify = False

        # Create and mount an adapter that specifies retry info
        adapter = HTTPAdapter(max_retries=Retry(total=retries*3,
                                                connect=retries,
                                                read=retries,
                                                redirect=10,
                                                status=retries,
                                                status_forcelist=[
                                                    500, 502, 503, 504],
                                                backoff_factor=0.3,
                                                raise_on_status=True))
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def doHttpRequest(self,
                      url: str,
                      method: str = "GET",
                      data: Dict = {},
                      stream: bool = False):
        """
        Makes a GET or POST request to URL returning response object

        Parameters: url (str): Request URL method (str): GET or POST data
        (Dict): Post data

        Returns: str: The text content of the request or None
        """
        response_return = None

        try:
            response_return = self.session.request(method=method,
                                                   url=url,
                                                   data=data,
                                                   stream=stream,
                                                   timeout=self.timeout)
            response_return.raise_for_status()
        except BaseException as e:
            print(str(e))
            raise e

        return response_return

    def doTextRequest(self,
                      url: str,
                      method: str = "GET",
                      data: Dict = {}) -> str:
        """
        Makes a GET or POST request to URL returning the text content of the URL

        Parameters: url (str): Request URL method (str): GET or POST data
        (Dict): Post data

        Returns: str: The text content of the request or None
        """
        strReturn = None

        response = self.doHttpRequest(url=url,
                                      method=method,
                                      data=data)

        if response:
            strReturn = response.text

        return strReturn

    def get_filename_from_cd(self, cd: str) -> str:
        """
        Get filename from content-disposition
        """
        filename: str = None
        if cd:
            fname = re.findall('filename=["\']*([\w\s:.]+)["\']*', cd)
            if len(fname) > 0:
                filename = fname[0]
        return filename

    def constructPath(self, file_or_dir: str, filename: str = None, prefer_filename: bool = True) -> Path:
        """
        """
        path_return: Path = None

        if not file_or_dir:
            file_or_dir = "."

        path_return = Path(file_or_dir)

        if filename:
            if path_return.is_dir():
                path_return = path_return / Path(filename)
            else:
                if prefer_filename:
                    path_return = path_return.parent / Path(filename)

        return path_return

    def downloadBinaryFile(self,
                           url: str,
                           filename: str = ".",
                           method: str = "GET",
                           data: Dict = {},
                           prefer_cd_filename: bool = True,
                           progress_label: str = None,
                           noprogress: bool = None) -> Path:
        """
        """
        path_return: Path = self.constructPath(filename)

        success: bool = False

        for attempt in range(1, self.retries+1):
            try:
                response = self.doHttpRequest(
                    url, method, data, stream=True)

                if not response:
                    path_return = None
                    response.raise_for_status()
                else:
                    file_size = int(response.headers.get('Content-Length'))

                    cd = response.headers.get('Content-Disposition')
                    cd_filename = self.get_filename_from_cd(cd)
                    if prefer_cd_filename:
                        if (cd):
                            path_return = self.constructPath(
                                filename, self.get_filename_from_cd(cd), prefer_filename=prefer_cd_filename)

                    if not path_return or path_return.is_dir():
                        raise RuntimeError(
                            f"download filename not specified and could not be determined ({str(path_return)}).")

                    if not progress_label:
                        progress_label = path_return.name

                    path_return.parent.mkdir(parents=True, exist_ok=True)

                    with open(str(path_return), 'wb') as fd:
                        chunk_size: int = self.chunk_size
                        downloaded: int = 0
                        with tqdm(total=file_size, desc=progress_label, unit="B", disable=noprogress, smoothing=0.1) as pbar:
                            try:
                                for chunk in response.iter_content(chunk_size=chunk_size):
                                    if (chunk):
                                        written: int = fd.write(chunk)
                                        pbar.update(written)
                            except BaseException as ex:
                                pbar.set_description(f"Failed #{attempt}")
                                raise ex
                    if self.check_file_size:
                        dl_file_size = path_return.stat().st_size
                        if dl_file_size != file_size:
                            logging.debug(
                                f"Downloaded file '{path_return.name}' has invalid size of {dl_file_size} and should be {file_size}")
                            raise RuntimeError(
                                f"Downloaded file '{path_return.name}' has invalid size of {dl_file_size} and should be {file_size}")

                    success = True
                    break
            except BaseException as e:
                logging.exception(
                    f"Error downloading file '{path_return.name}': {str(e)}")
                if attempt < self.retries:
                    logging.debug(f"Retrying {attempt+1} of {self.retries}")
                    time.sleep(attempt)

        if not success:
            if path_return.exists():
                os.remove(path_return)
            logging.debug(
                f"Could not download '{path_return.name}'.  {self.retries} failed attempts.")
            raise RuntimeError(
                f"Could not download '{path_return.name}'.  {self.retries} failed attempts.")

        return path_return
