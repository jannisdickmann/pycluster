"""
PyCluster is an application to conveniently schedule jobs to a slurm cluster.

Usage:
    pycluster.py create <config-type>
    pycluster.py run <config> [options]
    pycluster.py interactive <partition>
    pycluster.py [options]

Options:
    -h, --help                       Show this screen
    -v, --verbose                    Verbose execution of jobs (optional)
    -p, --partition <str>            Overwrite the partition when using the run command.
    -j, --jobs <str>                 Run only specific jobs (e.g. 4,8,20,24-48:4) which are compatible with the array arguments in the <config> file.
    -d, --dry                        If given, will not submit to cluster, but only create inputfiles.

Cluster configuration will be read from <config>.
In create mode a cluster configuration will be created.
"""

import docopt
import os
import pycluster
from pycluster.createconfig import CreateConfig
from pycluster.cluster import Cluster, InteractiveCluster


def main(args):
    if args['run'] and args['<config>'] is not None:
        config_filename = args['<config>']
        cluster_config = pycluster.parse_config(config_filename, 'config')
        cluster = Cluster(cluster_config, partition=args['--partition'], dry=args['--dry'], jobs=args['--jobs'])
        cluster.run()
    elif args['create'] and args['<config-type>'] is not None:
        # Create config file
        cluster_config = pycluster.parse_config(
            os.path.join(os.path.dirname(__file__), 'configs', '{}.json'.format(args['<config-type>'])),
            'config-template'
        )
        config = CreateConfig(cluster_config, args['<config-type>'])
        config.write()
    elif args['interactive'] and args['<partition>'] is not None:
        cluster = InteractiveCluster(partition=args['<partition>'], dry=args['--dry'])
        cluster.run()
    else:
        print('Please either provide a cluster configuration file using "pycluster.py run <config>" or invoke '
              '"pycluster.py create <config-type>".')
    print('Goodbye :-)')


if __name__ == '__main__':
    # Parse the command line arguments:
    args = docopt.docopt(__doc__)
    main(args)
