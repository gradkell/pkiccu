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


from pkiccu.http_utils import HttpUtils
from pkiccu.x509_utils import X509Utils
from tqdm import tqdm
from pathlib import Path
import shutil
import sys
import logging


class UrlDownloader:

    def __init__(self, http_utils: HttpUtils = None):
        self.http_utils = http_utils
        if not self.http_utils:
            self.http_utils = HttpUtils()

    def download_files(self, downloads: list, noprogress: bool = None):
        if downloads:
            with tqdm(total=len(downloads), desc="Downloading...", unit="Files", disable=noprogress, smoothing=0.1) as pbar:
                for download in downloads:
                    try:
                        src: str = download.get('src')
                        dst: str = download.get('dst')
                        typ: str = download.get('type', "unk")
                        fmt: str = download.get('fmt', "bin")
                        if not src or not dst or not typ or not fmt:
                            raise RuntimeError(
                                f"Invalid download spec: {download}")
                        else:
                            path_dst = Path(dst)
                            pbar.set_description(path_dst.name)
                            skip = typ == "cer" and path_dst.exists() and path_dst.stat().st_size > 0
                            if not skip:
                                logging.debug(
                                    f"Downloading URL '{src}' to file '{dst}'")
                                path_dl = self.http_utils.downloadBinaryFile(url=src,
                                                                             filename=dst,
                                                                             progress_label=path_dst.name,
                                                                             noprogress=True)
                                if path_dl.exists() and typ.lower() == 'cer' and fmt.lower() == 'pem':
                                    X509Utils.write_cert_pem_to_der(path_dl)
                                if path_dl.exists() and typ.lower() == 'cer' and fmt.lower() == 'pem':
                                    X509Utils.write_cert_pem_to_der(path_dl)
                    except BaseException as ex:
                        logging.exception(
                            f"Error downloading file: '{str(ex)}'")
                        print(str(ex), file=sys.stderr)
                    pbar.update(1)
                pbar.set_description("File Downloads Complete")
