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

# Building PKICCU

This file is for developers or system admins who want to build PKICCU for some
reason.

Contents:

- [Requirements](#requirements)
- [Build procedures](#build-procedures)
  - [Download and Extract Source
    Distribution](#download-and-extract-source-distribution)
  - [Setup Python Environment with
    Pipenv](#setup-the-build--environment-with-pipenv)
  - [Run the build script](#run-the-build-script)
  - [Examine the Distribution Directory](#examine-the-distribution-directory)

## Requirements

There are two main requirements to building PKICCU:

- **Python 3**: We have tested python versions 3.6.3 and 3.7.2, although it may
  work fine with previous versions of Python 3.
- **pipenv**: used for virtual environments and dependency resolution

Other dependencies are installed automatically by pipenv.

_NOTE: it may be possible to build without pipenv, but that's up to you to
figure out._

You need to start with at least Python 3.6 or higher with pip. If you don't
have pipenv, it can be installed easily with `pip install pipenv`.

## Build procedures

#### Download and Extract Source Distribution

PKICCU distributions are archived in ZIP format. Just unzip the source
distribution and change directories into the source distribution directory.

#### Setup the Build Environment with Pipenv

Next, just run `pipenv shell`. This should create a virtual environment and open
a shell set with the proper environment variable to use the environment.

_NOTE: if you aren't using the same version of Python as specified in the
Pipfile and Pipfile.lock files, you will get a warning from pipenv. You might
can ignore this warning, but it is suggested that you edit Pipfile and
Pipfile.lock files to specify the version of Python that you are using._

Next run `pipenv install`. This downloads all the requirements (including
pyinstaller) and installs them in the Python virtual environment.

You're build environment is now set up.

#### Run the build script

PKICCU comes with a build script named `build.py` that builds PKICCU and
packages source and binary distributions.

The `build.py` script should be executable on Linux or Mac systems, but if not,
make it executable with `chmod +x build.py`.

Next just execute the `build.py` script. On Linux or Mac, you can just run
`./build.py`. On Windows, you need to run `python build.py`.

_The build script runs **[pyinstaller](https://www.pyinstaller.org/)** to create
executable files. Then it packages up the required files in ZIPs. To build
binary releases for multiple platforms, you must run build PKICCU on each
platform. This is just the way pyinstaller works._

If there are errors, you'll just have to work with it and figure it out.

#### Examine the Distribution Directory

The build script makes distribution directory named "dist" containing two ZIP
files:

- **pkiccu\_&lt;version&gt;\_src.zip**: the source distribution
- **pkiccu\_&lt;version&gt;\_&lt;platform&gt;.zip**: the binary distribution

where &lt;version&gt; is the version of PKICCU from the src/pkiccu/version.py
file and &lt;platform&gt; is "lnx", "mac", or "win".

Congrats! The build is complete!
