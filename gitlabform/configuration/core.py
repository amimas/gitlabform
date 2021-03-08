import os
import logging
import sys

import yaml
from pathlib import Path


class ConfigurationCore:

    config = None
    config_dir = None

    def __init__(self, config_path=None, config_string=None):

        if config_path and config_string:
            logging.fatal(
                "Please initialize with either config_path or config_string, not both."
            )
            sys.exit(1)

        try:
            if config_string:
                logging.info("Reading config from provided string.")
                self.config = yaml.safe_load(config_string)
                self.config_dir = "."
            else:  # maybe config_path
                if "APP_HOME" in os.environ:
                    # using this env var should be considered unofficial, we need this temporarily
                    # for backwards compatibility. support for it may be removed without notice, do not use it!
                    config_path = os.path.join(os.environ["APP_HOME"], "config.yml")
                elif not config_path:
                    # this case is only meant for using gitlabform as a library
                    config_path = os.path.join(
                        str(Path.home()), ".gitlabform", "config.yml"
                    )
                elif config_path in [os.path.join(".", "config.yml"), "config.yml"]:
                    # provided points to config.yml in the app current working dir
                    config_path = os.path.join(os.getcwd(), "config.yml")

                logging.info("Reading config from file: {}".format(config_path))

                with open(config_path, "r") as ymlfile:
                    self.config = yaml.safe_load(ymlfile)
                    logging.debug("Config parsed successfully as YAML.")

                # we need config path for accessing files for relative paths
                self.config_dir = os.path.dirname(config_path)

                if self.config.get("example_config"):
                    logging.fatal(
                        "Example config detected, aborting.\n"
                        "Haven't you forgotten to use `-c <config_file` switch?\n"
                        "If you created your config based on the example one then please remove "
                        "'example_config' key."
                    )
                    sys.exit(1)

            self.find_almost_duplicates()

        except (FileNotFoundError, IOError):
            raise ConfigFileNotFoundException(config_path)

        except Exception:
            if config_path:
                raise ConfigInvalidException(config_path)
            else:
                raise ConfigInvalidException(config_string)

    def get(self, path, default=None):
        """
        :param path: "path" to given element in YAML file, for example for:

        group_settings:
          sddc:
            deploy_keys:
              qa_puppet:
                key: some key...
                title: some title...
                can_push: false

        ..a path to a single element array ['qa_puppet'] will be: "group_settings|sddc|deploy_keys".

        To get the dict under it use: get("group_settings|sddc|deploy_keys")

        :return: element from YAML file (dict, array, string...)
        """
        tokens = path.split("|")
        current = self.config

        try:
            for token in tokens:
                current = current[token]
        except:
            if default is not None:
                return default
            else:
                raise KeyNotFoundException

        return current

    def find_almost_duplicates(self):

        # in GitLab groups and projects names are de facto case insensitive:
        # you can change the case of both name and path BUT you cannot create
        # 2 groups which names differ only with case and the same thing for
        # projects. therefore we cannot allow such entries in the config,
        # as they would be ambiguous.

        for path in [
            "group_settings",
            "project_settings",
            "skip_groups",
            "skip_projects",
        ]:
            if self.get(path, 0):
                almost_duplicates = self._find_almost_duplicates(path)
                if almost_duplicates:
                    logging.fatal(
                        f"There are almost duplicates in the keys of {path} - they differ only in case.\n"
                        f"They are: {', '.join(almost_duplicates)}"
                        f"This is not allowed as we ignore the case for group and project names."
                    )
                    sys.exit(1)

    def _find_almost_duplicates(self, configuration_path):
        """
        Checks given configuration key and reads its keys - if it is a dict - or elements - if it is a list.
        Looks for items that are almost the same - they differ only in the case.
        :param configuration_path: configuration path, f.e. "group_settings"
        :return: list of items that have almost duplicates,
                 or an empty list if none are found
        """

        dict_or_list = self.get(configuration_path)
        if isinstance(dict_or_list, dict):
            items = dict_or_list.keys()
        else:
            items = dict_or_list

        items_with_lowercase_names = [x.lower() for x in items]

        # casting these to sets will deduplicate the one with lowercase names
        # lowering its cardinality if there were elements in it
        # that before lowering differed only in case
        if len(set(items)) != len(set(items_with_lowercase_names)):

            # we have some almost duplicates, let's find them
            almost_duplicates = []
            for first_item in items:
                occurrences = 0
                for second_item in items_with_lowercase_names:
                    if first_item.lower() == second_item.lower():
                        occurrences += 1
                        if occurrences == 2:
                            almost_duplicates.append(first_item)
                            break
            return almost_duplicates

        else:
            return []


class ConfigFileNotFoundException(Exception):
    pass


class ConfigInvalidException(Exception):
    pass


class KeyNotFoundException(Exception):
    pass
