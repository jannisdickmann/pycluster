import json
import os
from pycluster import *
from jinja2 import Template
import getpass


class CreateConfig:
    def __init__(self, config, configtype):
        """
        Generate a configuration file given a template for this configuration type. Query the user for some variables.
        Finally write the configuration file to disk.
        :param config: The template configuration file (resides inside the templates folder)
        :param configtype: The type of the configuration (corresponds to filename inside the templates folder)
        """
        self.config = config
        self.config['configtype'] = configtype
        self.config['output_directory'] = os.path.expanduser(self.config['output_directory'])

        # make username available
        self.config['user'] = getpass.getuser()

        print('Please enter the following values. Leave your answer empty (press enter) to accept default values.')

        # First process array variables
        for key in ['first', 'step', 'last']:
            self.config['array'][key] = self.get_user_input(self.config['array'], key, prepend='array ',
                                                            variabletype=int)

        if (self.config['array']['last'] - self.config['array']['first'] ) % self.config['array']['step'] != 0:
            raise ValueError('The last index {:d} is not reachable with a step size of {:d} from the first index '
                             '{:d}.'.format(self.config['array']['last'], self.config['array']['step'],
                                            self.config['array']['first']))

        # Then process clsuter variables
        for key in ['partition', 'max_memory', 'max_time', 'mail']:
            self.config['cluster'][key] = self.get_user_input(self.config['cluster'], key, prepend='cluster ')

        # Fill values where user must be queried
        for key in self.config.keys():
            if key != 'array' and key != 'cluster':
                self.config[key] = self.get_user_input(self.config, key)

        # Generate projectname and output directory (they may depend on other values)
        self.config['project_name'] = Template(self.config['project_name']).render(self.config)
        self.config['output_directory'] = Template(self.config['output_directory']).render(self.config)

    @staticmethod
    def get_user_input(dictionary, key, prepend='', variabletype=None):
        """
        Query the user for a specific information to fill to the configuration dict. If information is already there,
        and does not need to be queried, return the dict as it is. Values that need to be queried are indicated by
        setting them to {"default": "xxx"}, where "xxx" is a default value. The user can accept the default value
        by hitting enter.
        :param dictionary: The configuration dict
        :param key: The key from the configuration dict to be queried to the user
        :param prepend: Prepend output with a string (optional)
        :param variabletype: Convert input to a specific type. If not given, str is assumend
        :return: The potentially modified value.
        """
        if variabletype is None:
            variabletype = str
        if isinstance(dictionary[key], dict):
            if 'default' in dictionary[key]:
                return typedvariableinput(key, dictionary[key]['default'], variabletype, prepend)
            elif 'random_int' in dictionary[key] or 'random_float' in dictionary[key]:
                return dictionary[key]
            else:
                return dictionary[key]
        else:
            return dictionary[key]

    def write(self):
        """
        Write the configuration dict to disk.
        """
        filename = '{}.cluster.json'.format(self.config['project_name'])
        directory = self.config['output_directory'] + '/' + self.config['project_name']
        os.makedirs(directory, exist_ok=True)
        file = os.path.join(directory, filename)
        if os.path.isfile(file):
            write_config = parseynanswer(
                'A configuration file already exists in "{}". Do you want to overwrite?'.format(file)
            )
        else:
            write_config = True

        if write_config:
            with open(file, 'w') as outfile:
                json.dump(self.config, outfile, indent=4, sort_keys=False)
                print('A cluster configuration was written to {}. Start the cluster run by passing this file as an '
                      'argument to pycluster.py.'.format(file))
