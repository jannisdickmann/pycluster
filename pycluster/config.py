import json
import sys
import os

__all__ = [
    'parse_config',
    'parse_settings',
    'get_partition_idx'
]


def parse_config(filename, configtype):
    """
    Read a configuration JSON file from disk
    :param filename: The filename of the JSON file
    :param configtype: Type of configuration to tailor error messages.
    :return: The JSON file as dict.
    """
    try:
        with open(filename) as f:
            data = json.load(f)
    except FileNotFoundError:
        msg = 'The {} file <{}> does not exist.'.format(configtype, filename)
        if configtype == 'config':
            msg += ' Please create a run configuration file by invoking <pycluster.py --create>.'
        elif configtype == 'config-template':
            msg += ' Please create a cluster configuration file in the /configs folder.'
        elif configtype == 'settings':
            msg += ' A settings file is required. Please restore it from the repository.'
        print(msg)
        sys.exit(1)
    return data


def parse_settings():
    """
    Read the settings JSON file from disk
    :return: The JSON file as dict.
    """
    filename = os.path.abspath(os.path.join(os.path.dirname(__file__), '../settings.json'))
    return parse_config(filename, 'settings')


def get_partition_idx(settings, partition):
    """
    Returns the index of a given partition within the settings dict.
    :param settings: A settings dict generated with parse_settings()
    :param partition: The partition to search
    :return: The index of the partition within the settings dict
    :raises: Exits with error message if partition not found
    """
    for i in range(len(settings['partitions'])):
        if settings['partitions'][i]['name'] == partition:
            # return index if partition was found
            return i
    # partition was not found
    msg = 'The partition {} was not found in the settings.json configuration.'.format(partition)
    print(msg)
    sys.exit(1)
