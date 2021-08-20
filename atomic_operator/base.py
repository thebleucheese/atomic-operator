import os
import re
import sys
import zipfile
from io import BytesIO
import platform
import subprocess
import requests
from .config import Config
from .utils.logger import LoggingBase
from .utils.exceptions import MalformedFile


class Base(metaclass=LoggingBase):

    CONFIG = None
    ATOMIC_RED_TEAM_REPO = 'https://github.com/redcanaryco/atomic-red-team/zipball/master/'
    command_map = {
        'command_prompt': {
            'windows': 'C:\\Windows\\System32\\cmd.exe',
            'linux': '/bin/sh',
            'macos': '/bin/sh',
            'default': '/bin/sh'
        },
        'powershell': {
            'windows': 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe'
        },
        'sh': {
            'linux': '/bin/sh',
            'macos': '/bin/sh'
        },
        'bash': {
            'linux': '/bin/bash',
            'macos': '/bin/bash'
        }
    }

    def clean_output(self, data):
        """Decodes data and strips CLI garbage from returned outputs and errors

        Args:
            data (str): A output or error returned from subprocess

        Returns:
            str: A cleaned string which will be displayed on the console and in logs
        """
        # Remove Windows CLI garbage
        data = re.sub(r"Microsoft\ Windows\ \[version .+\]\r?\nCopyright.*(\r?\n)+[A-Z]\:.+?\>", "", data)
        return re.sub(r"(\r?\n)*[A-Z]\:.+?\>", "", data)

    def download_atomic_red_team_repo(self, save_path, **kwargs):
        """Downloads the Atomic Red Team repository from github

        Args:
            save_path (str): The path to save the downloaded and extracted ZIP contents

        Returns:
            str: A string of the location the data was saved to.
        """
        response = requests.get(Base.ATOMIC_RED_TEAM_REPO, stream=True, **kwargs)
        z = zipfile.ZipFile(BytesIO(response.content))
        z.extractall(save_path)
        return z.namelist()[0]

    def format_config_data(self, config_file):
        """Parses a provide path to a configuration data file (yaml).

        Args:
            config_file (str): A path to a valid config_file.

        Raises:
            FileNotFoundError: Raises if provided a config_file path that does not exist
            MalformedFile: Raises if the provided config file does not meet the defined format

        Returns:
            dict: A dictionary of configuration values used to drive atomic-operator execution of Atomics
        """
        return_dict = {}
        if config_file:
            if not os.path.exists(config_file):
                raise Exception('Please provide a config_file path that exists')
            from .atomic.loader import Loader
            config_file = Loader().load_technique(config_file)
            
            if not config_file.get('atomic_tests') and not isinstance(config_file, list):
                raise  MalformedFile('Please provide one or more atomic_tests within your config_file')
            for item in config_file['atomic_tests']:
                if item.get('guid') not in return_dict:
                    return_dict[item['guid']] = {}
                if item.get('input_arguments'):
                    for key,val in item['input_arguments'].items():
                        return_dict[item['guid']].update({
                            key: val.get('value')
                        })
        return return_dict

    def get_local_system_platform(self):
        """Identifies the local systems operating system platform

        Returns:
            str: The current/local systems operating system platform
        """
        os_name = platform.system().lower()
        if os_name == "darwin":
            return "macos"
        return os_name

    def get_abs_path(self, value):
        """Formats and returns the absolute path for a path value

        Args:
            value (str): A path string in many different accepted formats

        Returns:
            str: The absolute path of the provided string
        """
        return os.path.abspath(os.path.expanduser(os.path.expandvars(value)))

    def show_details(self, value):
        """Displays the provided value string if Base.CONFIG.show_details is True

        Args:
            value (str): A string to display if selected in config.
        """
        if Base.CONFIG.show_details:
            self.__logger.info(value)

    def prompt_user_for_input(self, title, input_object):
        """Prompts user for input values based on the provided values.
        """
        print(f"""
Inputs for {title}:
    Input Name: {input_object.name}
    Default:     {input_object.default}
    Description: {input_object.description}
""")
        print(f"Please provide a value for {input_object.name} (If blank, default is used):",)
        value = sys.stdin.readline()
        if bool(value):
            return value
        return input_object.default

    def print_process_output(self, command, return_code, output, errors):
        """Outputs the appropriate outputs if they exists to the console and log files

        Args:
            command (str): The command which was ran by subprocess
            return_code (int): The return code from subprocess
            output (bytes): Output from subprocess which is typically in bytes
            errors (bytes): Errors from subprocess which is typically in bytes
        """
        else:
            self.__logger.info("(No output)")
        if errs:
            self.__logger.error("Errors: {}".format(self.clean_output(errs.decode("utf-8", "ignore"))))

    def execute_subprocess(self, executor, command, cwd):
        """Executes commands using subprocess

        Args:
            executor (str): An executor or shell used to execute the provided command(s)
            command (str): The commands to run using subprocess
            cwd (str): A string which indicates the current working directory to run the command

        Returns:
            tuple: A tuple of either outputs or errors from subprocess
        """
        p = subprocess.Popen(
            executor, 
            shell=False, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, 
            env=os.environ, 
            cwd=cwd
        )
        try:
            outs, errs = p.communicate(
                bytes(command, "utf-8") + b"\n", 
                timeout=Base.CONFIG.command_timeout
            )
            if p.returncode != 0:
                self.__logger.warning(f"Command: {command} returned exit code {p.returncode}: {outs}")
            self.print_process_output(outs, errs)
            return outs, errs
        except subprocess.TimeoutExpired as e:
            # Display output if it exists.
            if e.output:
                self.__logger.warning(e.output)
            if e.stdout:
                self.__logger.warning(e.stdout)
            if e.stderr:
                self.__logger.warning(e.stderr)
            self.__logger.warning("Command timed out!")

            # Kill the process.
            p.kill()
            return "", ""
