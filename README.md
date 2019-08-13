<!--
Copyright 2019 Gradkell Systems, Inc. Author: Mike R. Prevost,
mprevost@gradkell.com

This file is part of PKICCU.

PKICCU is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

PKICCU is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <https://www.gnu.org/licenses/>.
-->

# PKICCU: PKI Certificate and CRL Updater

Contents:

- [About](#about)
- [Why PKICCU?](#why-pkiccu)
- [What Can PKICCU Do?](#what-can-pkiccu-do)
  - [Keep Certs and CRL Files Updated](#keep-certs-and-crl-files-updated)
  - [Run Integration Scripts](#run-integration-scripts)
  - [Generate Certificate Bundles for Apache Web
    Servers](#generate-certificate-bundles-for-apache-web-servers)
- [What CAN'T PKICCU Do?](#what-cant-pkiccu-do)
  - [No Root CA certificates from DoD
    PKI](#no-root-ca-certificates-from-dod-pki)
  - [Limited Support for Non-DoD PKIs](#limited-support-for-non-dod-pkis)
- [Using PKICCU](#using-pkiccu)
  - [Configuration](#configuration)
  - [Execution](#execution)
  - [Logging](#logging)
- [Getting Help](#getting-help)

## About

PKICCU _(pronounced 'peek-ih-choo')_ is the "PKI Certificate and CRL Updater".
PKICCU is a highly configurable utility that downloads PKI certificates, CRLs
and other files with special support for the US DoD PKI environment. PKICCU can
create openssl-style certificate bundles which are used with web servers such as
Apache to configure SSL client-certificate validation. PKICCU can also run user
provided external scripts to integrate the certificate when the update
operations are complete. Actually, PKICCU can be used whenever you need to
download some files and then run scripts afterward.

_PKICCU supports Windows, Linux and Mac. Although PKICCU was developed in
Python, it has been packaged into a single, self-contained, executable program
that has no external dependencies (not even Python). There is nothing else to
install or configure._

## Why PKICCU?

PKICCU helps websites keep their certificates and CRLs up to date. Although
PKICCU can download certs, CRLs and other files from any source, it has special
support for the DoD PKI environment. The original target environment was US DoD
websites that update certs and CRLs from the DoD PKI. Since the DoD PKI is one
of the largest PKIs in the world, they often add new CAs. These new CAs need to
be configured into other software such as web servers or some users won't be
able to access their systems. PKICCU helps automate this process so that new CAs
are integrated into systems automatically. PKICCU handles all the certificate
and CRL discovery and downloading. All you have to do is provide the scripts to
integrate them into your systems.

PKICCU includes features that make it robust and secure. There are many features
to make sure that downloads complete successfully and that the downloaded data
is correct. PKICCU can perform full certificate validation on SSL certs to
ensure that the website you are downloading from is genuine. And, since
downloads sometimes fail, especially for large files, PKICCU will retry the
download a user configurable number of times before giving up. PKICCU also
employs several layers of data integrity checks on downloaded data. First, the
file size of the download is checked against the file size reported by the web
server when the download started. Additionally, if a file hash code was
available on the download site (e.g., cert hashes on the DISA PKI sites), the
downloaded file is hashed and checked against the published has value. On top of
that, cert and CRL files can be parsed after download is complete to ensure that
they are valid files.

PKICCU is designed to as a cron job or scheduled task so that it runs at regular
intervals. Each time it runs, it will perform all its configured functions.

## What Can PKICCU Do?

#### Keep Certs and CRL Files Updated

First and foremost, PKICCU downloads certificates and CRLs and keeps a directory
structure up to date with the most recent files. In the DoD environment, new CA
certificates and CRLs are automatically detected. This is done by querying a
DISA website(s) that holds all the certs and CRLs issued by DoD. PKICCU can also
access the DoD JITC test PKI site.

On non-DoD PKIs PKICCU can be configured with URLs to download. These can be
certs, CRLs, or other files you may need. All these files are available to your
scripts.

#### Run Integration Scripts

When the downloads are complete, PKICCU can run user developed scripts or
programs so that the new certs and CRLs can be integrated with the various
webservers and other systems that need it.

_PKICCU also comes with a program that can execute the DBsign CRL Updater to
update certs and CRLs in the DBsign digital signature system._

#### Generate Certificate Bundles for Apache Web Servers

The Apache web server's mod_ssl SSL/TLS implementation uses OpenSSL-style
certificate bundles to configure various aspects of its SSL subsystem.
Specifically the following:

- SSLCACertificateFile: a list of CA certificates used to validate end user SSL
  client authentication certificates (contains intermediate and root
  certificates)
- SSLCADNRequestFile: a list of intermediate CA certificates used to filter
  which certificates are presented to the end user during SSL client
  authentication (typically contains only intermediates)

PKICCU can generate certificate bundles to be used by Apache for this purpose.
Scripts can then be written for PKICCU that copy these files into the correct
locations for Apache.

## What CAN'T PKICCU Do?

#### No Root CA certificates from DoD PKI

PKICCU can't download root CA certs from DISA. This is because DISA doesn't
publish them, and for good reason. Since root CA certs are explicitly trusted,
they need to come from a trusted source. Root certificates usually don't change
and they are not issued frequently. The root certificates can be manually added
to PKICCU's PKI data directory structure so that they can be used in certificate
bundles, etc. In DoD, you can probably get the root certificates from a DoD
Windows computer in the Trusted Certification Authorities certificate store.

#### Limited Support for Non-DoD PKIs

PKICCU cannot automatically discover when new CAs are added to non-DoD PKIs.
This is because PKICCU uses the DISA PKI website to determine when CA
certificates are available. And, if DISA changes the way their website works too
much, then updates to PKICCU will have to be made.

## Using PKICCU

#### Configuration

Before using PKICCU, you should edit the configuration file, `pkiccu.cfg`. The
configuration file is in YAML format, which is a superset of JSON. It is
suggested that you keep the JSON-like format. Comments begin with the pound or
hash character, "#", and continue to the end of the line.

The default configuration should be a good starting point. Each section and
variable in the default configuration file is documented in comments, so the
documentation will not be duplicated here.

The variables section contains much of what you might want to change. This
section is just a list of name/value pairs that define "variables" that will be
replaced all configuration item values. For example, if you define a variable
named "foo" with a value of "bar", then anywhere else in the configuration file,
the string "{foo}" will be replaced with "bar".

The other things you will want to change are the default configurations in the

- `disa_downloader`,
- `url_downloader`,
- `cert_bundler`, and
- `scripts` sections.

In the `disa_downloader` section, you can comment out the `jitc` section if you
don't want to download from the DoD JITC Test PKI. If you don't use the DoD PKI,
then you can comment out both the `prod` and `jitc` sections.

In the `url_downloader`, you should adjust these to suite your environment. The
`url_downloader` section just has bogus examples. If you don't need this
functionality, just comment out or remove the items in the `downloads` list.

The `cert_bundler` section will also have to be adjusted to your environment. If
you don't use use this functionality, just comment out or remove everything in
the `bundles` section.

The `scripts` section should also be adjusted to your environment. If you don't
use this functionality, just comment out or remove everything in the `run_list`
list.

#### Execution

The PKICCU executable is named `pkiccu` or `pkiccu.exe` on Windows. Its command
line arguments are documented in its help message which can be displayed with
`pkiccu --help`. Documentation of the command line arguments will not be
duplicated here.

PKICCU can be executed on the command line or via as an automated background
process. When executed as an interactive command line process, it displays
text-based progress bars that give updates about what it is currently doing. As
a background process, the progress bars are automatically disabled.

#### Logging

Logging is configured and documented in the configuration file. By default, a
log file named `PKICCU_<timestamp>.log` is created in the `./logs` directory.
The location of the log file as well as the log level are configured in the
configuration file. A new log file can be created upon each execution (the
default), of a single log file can be appended to.

## Getting Help

PKICCU is a tiny open source project and there is no formal technical support
provided by anyone. However, you can email us at "support AT gradkell DOT com"
and we might try to help you. `;)`
