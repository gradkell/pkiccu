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


from typing import Dict
import datetime
from pathlib import Path
from cryptography.x509 import Certificate, CertificateRevocationList, load_der_x509_certificate, load_pem_x509_certificate, load_der_x509_crl, load_pem_x509_crl
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


class X509Utils:

    def load_cert_der(fn: str) -> Certificate:
        cert_return = None
        if (fn and Path(fn).exists()):
            with open(fn, "rb") as file:
                data = file.read()
                if data and len(data) > 0:
                    cert_return = load_der_x509_certificate(
                        data, default_backend())
        return cert_return

    def load_crl_der(fn: str) -> CertificateRevocationList:
        crl_return = None
        if (fn and Path(fn).exists()):
            with open(fn, "rb") as file:
                data = file.read()
                if data and len(data) > 0:
                    crl_return = load_der_x509_crl(
                        data, default_backend())
        return crl_return

    def load_cert_pem(fn: str) -> Certificate:
        cert_return = None
        if (fn and Path(fn).exists()):
            with open(fn, "rb") as file:
                data = file.read()
                if data and len(data) > 0:
                    cert_return = load_pem_x509_certificate(
                        data, default_backend())
        return cert_return

    def load_crl_pem(fn: str) -> CertificateRevocationList:
        crl_return = None
        if (fn and Path(fn).exists()):
            with open(fn, "rb") as file:
                data = file.read()
                if data and len(data) > 0:
                    crl_return = load_pem_x509_crl(
                        data, default_backend())
        return crl_return

    def cert_get_subject(cert: Certificate) -> str:
        return cert.subject.rfc4514_string()

    def cert_get_issuer(cert: Certificate) -> str:
        return cert.issuer.rfc4514_string()

    def cert_get_valid_from(cert: Certificate) -> datetime:
        return cert.not_valid_before

    def cert_get_valid_to(cert: Certificate) -> datetime:
        return cert.not_valid_after

    def convert_cert_pem(cert: Certificate, include_info: bool = True) -> str:
        pem_return = None
        if cert:
            if include_info:
                pem_return = "################################################################\n"
                pem_return += f"Subject: {X509Utils.cert_get_subject(cert)}\n"
                pem_return += f"Issuer:  {X509Utils.cert_get_issuer(cert)}\n"
                pem_return += f"Valid From: {X509Utils.cert_get_valid_from(cert)} GMT\n"
                pem_return += f"Valid To:   {X509Utils.cert_get_valid_to(cert)} GMT\n"
            pem_return += cert.public_bytes(
                encoding=serialization.Encoding.PEM).decode("ascii")
        return pem_return

    def convert_cert_der(cert: Certificate) -> str:
        der_return = None
        if cert:
            der_return += cert.public_bytes(
                encoding=serialization.Encoding.DER)
        return der_return

    def read_der_cert_pem(fn: str, include_info: bool = True) -> str:
        pem_return: str = None
        cert = X509Utils.load_cert_der(fn)
        if cert:
            pem_return = X509Utils.convert_cert_pem(
                cert, include_info=include_info)
        return pem_return

    def write_cert_pem(cert: Certificate, fn: str, include_info: bool = True):
        if cert and fn:
            with open(fn, "w") as file:
                file.write(X509Utils.convert_cert_pem(
                    cert, include_info=include_info))

    def write_cert_der(cert: Certificate, fn: str, include_info: bool = True):
        if cert and fn:
            with open(fn, "wb") as file:
                file.write(X509Utils.convert_cert_der(cert))

    def rename_filename(fn_from: str, fn_to: str = None, new_ext: str = None) -> str:
        fn_return: str = None
        if fn_from:
            path_from = Path(fn_from)
            path_to = Path(fn_to) if (fn_to) else Path(fn_from)
            if (path_to.is_dir()):
                path_to = path_to / path_from.name
            if new_ext:
                path_to = path_to.parent / str(path_to.stem + "." + new_ext)
            fn_return = str(path_to)
        return fn_return

    def write_cert_der_to_pem(fn_in: str, fn_out: str = None, new_ext: str = None, include_info: bool = True):
        if fn_in:
            path_in = Path(fn_in)
            if path_in.exists():
                if (not new_ext):
                    new_ext = "crt" if path_in.suffix != "crt" else "pem"
                fn_new = X509Utils.rename_filename(path_in, fn_out, new_ext)
                cert = X509Utils.load_cert_der(path_in)
                if cert:
                    X509Utils.write_cert_pem(
                        cert, fn_new, include_info=include_info)

    def write_cert_pem_to_der(fn_in: str, fn_out: str = None, new_ext: str = None):
        if fn_in:
            path_in = Path(fn_in)
            if path_in.exists():
                if (not new_ext):
                    new_ext = "cer"
                fn_new = X509Utils.rename_filename(path_in, fn_out, new_ext)
                cert = X509Utils.load_cert_pem(path_in)
                if cert:
                    X509Utils.write_cert_der(cert, fn_new)
