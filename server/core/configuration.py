import os
import configparser


class Configuration:

    def __init__(self, configuration_name, configuration_path=None):
        self.__config = configparser.ConfigParser()
        self.__configuration_name = configuration_name

        if configuration_path is not None and os.path.exists(configuration_path):
            os.chdir(configuration_path)

    def read_config(self, section, option=None):
        self.__config.read(self.__configuration_name)

        if option is not None:
            if self.__config.has_option(section, option):
                return self.__config[section][option]

        return dict(self.__config.items(section))
