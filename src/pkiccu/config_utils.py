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


import yaml
from datetime import datetime


class ConfigUtils:

    def load(fn: str) -> dict:
        config_return = {}
        if fn:
            with open(fn, 'r') as f:
                config_return = yaml.safe_load(f)
            config_return = ConfigUtils.__do_config_replacements(config_return)
        return config_return

    def get(config: dict, param: str, default: any = None) -> any:
        val_return = default

        if config and param:
            param_list = param.split('.')
            if not isinstance(param_list, list):
                param_list = [param_list]

            val_return = ConfigUtils.__get(config, param_list, default)

        return val_return

    def __get(config: dict, param_list: list, default: any = None) -> any:
        val_return = default

        if config and param_list:
            param_next = param_list.pop(0)
            val_return = config.get(param_next)
            if val_return == None:
                val_return = default
            else:
                if len(param_list) > 0:
                    if isinstance(val_return, dict):
                        val_return = ConfigUtils.__get(
                            val_return, param_list, default)

        return val_return

    def __replace_variables(_val: any, variables: dict) -> any:
        val_return = _val
        if isinstance(_val, dict):
            val_return = {}
            for key in _val.keys():
                val_return[key] = ConfigUtils.__replace_variables(
                    _val.get(key), variables)
        elif isinstance(_val, list):
            val_return = []
            for item in _val:
                val_return.append(
                    ConfigUtils.__replace_variables(item, variables))
        elif isinstance(_val, str):
            for var in variables.keys():
                val_return = val_return.replace(
                    '{'+var+'}', variables.get(var))
        return val_return

    def __do_config_replacements(config: dict) -> dict:
        variables = config.get('variables')
        variables["_ts_start"] = datetime.now().replace(
            microsecond=0).isoformat()
        config['variables'] = ConfigUtils.__replace_variables(
            variables, variables)
        return ConfigUtils.__replace_variables(config, config['variables'])
