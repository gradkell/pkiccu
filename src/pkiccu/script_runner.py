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
from tqdm import tqdm
import subprocess
import os
import logging


class ScriptRunner:

    def run(script_def: dict):
        args = script_def.get("cmd_line", None)

        if isinstance(args, str):
            args = [args]

        if not args or not isinstance(args, list):
            raise RuntimeError(
                f"Process definition attribute 'cmd_line' not defined or is not a list.")
        else:
            name = script_def.get("name", "Unknown")
            shell = script_def.get("use_shell", False)
            cwd = script_def.get("current_working_dir", None)
            use_script_cwd = script_def.get("use_script_cwd", False)
            timeout = script_def.get("timeout", None)
            env = {**os.environ, **script_def.get("env", {})}

            # make argv[0] relative to the current working directory and not
            # to the script CWD
            if not use_script_cwd:
                arg0_path = Path(args[0])
                if arg0_path.exists():
                    args = [*args]
                    args[0] = str(arg0_path.resolve())

            logging.debug(f"Running script '{name}'...")
            try:
                completed = subprocess.run(args=args,
                                           shell=shell,
                                           cwd=cwd,
                                           timeout=timeout,
                                           env=env,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT,
                                           universal_newlines=True,
                                           check=True)
                if len(completed.stdout) > 0:
                    logging.debug(
                        f"Process output (stdout+stderr): \n--- BEGIN OUTPUT ({name}) ---\n{completed.stdout}--- END OUTPUT ({name}) ---")
                return completed
            except BaseException as e:
                logging.exception(f"Error running script '{name}': {str(e)}")
                raise RuntimeError(f"Script '{name}' failed: {str(e)}")

    def run_scripts(run_list: list, noprogress: bool = False):
        if isinstance(run_list, list):
            with tqdm(total=len(run_list), desc="Running Scripts...", unit="Scripts", disable=noprogress, smoothing=0.1) as pbar:
                for script_def in run_list:
                    try:
                        name = script_def.get("name", "Unknown")
                        pbar.set_description(name)
                        logging.info(f"Running script '{name}'")
                        completed = ScriptRunner.run(script_def)
                    except BaseException as e:
                        print(str(e))
                    pbar.update(1)
                pbar.set_description("Scripts complete.")
