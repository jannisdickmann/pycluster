import os
import stat
from jinja2 import Environment, FileSystemLoader
import copy
import shutil
import subprocess
import getpass
from pycluster.userinput import *
from pycluster.custom_filters import *
from pycluster.config import *
import sys


class Cluster:
    def __init__(self, config, partition=None, dry=False, jobs=None):
        """
        The constructor of the cluster class takes care of all preparation necessary before submitting jobs to the
        cluster, such as creating directories and generating input files.
        :param config: Cluster configuration file
        :param partition: Overwrite for the cluster patition (if None, then no overwrite)
        :param dry: Dry run: perform only peparatory steps, don't submit to cluster.
        """
        self.config = config
        self.dry = dry
        self.jobs = jobs

        # load settings
        self.settings = parse_settings()

        # make username available
        self.config['user'] = getpass.getuser()

        # overwrite partition and jobs option if requested
        if partition is not None:
            self.config['cluster']['partition'] = partition
        if jobs is not None:
            self.config['jobs'] = jobs

        self.env = Environment(
            loader=FileSystemLoader(os.path.abspath(os.path.join(os.path.dirname(__file__), '../templates'))),
            cache_size=0
        )
        self.env = setup_filters(self.env)
        self.template = self.env.get_template(self.config['inputfile'])
        self.jobtemplate = self.env.get_template('job.sh')
        self.localtemplate = self.env.get_template('local.sh')
        self._local_cpu_count = None

        # determine slurm configuration in advance
        self.partition_idx = get_partition_idx(self.settings, self.config['cluster']['partition'])
        self.slurmconf = self.settings['partitions'][self.partition_idx]['slurmconf']
        if 'job_init_command' in self.settings and self.settings['job_init_command']:
            self.job_init_command = self.settings['job_init_command'] + '; '
        else:
            self.job_init_command = ''
        self.priority_queue = self.settings['partitions'][self.partition_idx]['priority_queue']

        # create subdirectories
        createdirs = ['bash', 'err', 'log', 'inputfiles']
        if 'output_subdirectories' in self.config:
            createdirs += self.config['output_subdirectories']
        for createdir in createdirs:
            directory = os.path.join(self.config['output_directory'], self.config['project_name'], createdir)
            os.makedirs(directory, exist_ok=True)

        # copy executable if requested
        if 'copy_executable' in self.config and self.config['copy_executable']:
            fname = os.path.split(self.config['executable'])[1]
            dst = os.path.join(self.config['output_directory'], self.config['project_name'], 'bash', fname)
            shutil.copy(self.config['executable'], dst)
            self.config['executable'] = dst

        # generate job file and make it executable
        configuration = self.get_config_copy()
        output = self.jobtemplate.render(configuration)
        fname = self.get_sh_filename()
        with open(fname, 'w') as out_file:
            out_file.write(output)
        os.chmod(fname, os.stat(fname).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        # generate local execution file and make it executable
        configuration = self.get_config_copy()
        output = self.localtemplate.render(configuration)
        fname = self.get_sh_filename(filetype='local')
        with open(fname, 'w') as out_file:
            out_file.write(output)
        os.chmod(fname, os.stat(fname).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        # generate input files
        array_range = range(
            self.config['array']['first'],
            self.config['array']['last'] + self.config['array']['step'],
            self.config['array']['step']
        )
        print('Writing {:d} input files...'.format(len(array_range)))
        for iterator in array_range:
            self.reload_template()  # to avoid caching of the random filter
            configuration = self.get_config_copy(iterator)
            output = self.template.render(configuration)
            fname = self.get_output_filename(iterator)
            with open(fname, 'w') as out_file:
                out_file.write(output)

    def run(self):
        """
        Submits a job array to the cluster.
        """
        local_execution = self.config['cluster']['partition'] == 'local'

        if local_execution:
            command = self.get_sh_filename(filetype='local')
            if 'jobs' in self.config and self.config['jobs'] is not None:
                question = 'Warning:\n' \
                           'You are running a job array locally with the <jobs> option to specify execution only ' \
                           'of a few jobs. This is only supported on the slurm cluster and instead all jobs will ' \
                           'run. >>> Do you want to continue?'
                if not parseynanswer(question):
                    command = None
        else:
            if 'jobs' in self.config and self.config['jobs'] is not None:
                jobstring = self.config['jobs']
            else:
                jobstring = '{:d}-{:d}:{:d}'.format(
                    self.config['array']['first'],
                    self.config['array']['last'],
                    self.config['array']['step'],
                )
            command = '{}export SLURM_CONF={};' \
                      'sbatch --array={} -N1 {}'.format(
                self.job_init_command,
                self.slurmconf,
                jobstring,
                self.get_sh_filename()
            )

        if self.dry:
            print('Running in dry mode. Will not submit to cluster. Input files were created.')
            print('Cluster command is: <{}>.'.format(command))
        elif self.validate_config() and command is not None:
            subprocess.run(command, shell=True, executable='/bin/bash')
        else:
            print('Cluster job was not submitted due to user interruption.')

    def get_config_copy(self, iterator=None):
        """
        Get a deep copy of the configuration replacing some dependent variables.
        :param iterator: Make iterator available in configuration as variable.
        :return: The copy of the confriguration
        """
        # keep original structure, work on deep copy
        dictionary = copy.deepcopy(self.config)
        dictionary['iterator'] = iterator
        dictionary['cores_local'] = self._cpu_count()
        return dictionary

    def reload_template(self):
        """
        Resets the template file from disk
        """
        self.template = self.env.get_template(self.config['inputfile'])

    def get_output_filename(self, iterator):
        """
        Get the file name of the n-th input file
        :param iterator: The number of the input file
        :return: The file name
        """
        fname = os.path.join(
            self.config['output_directory'], self.config['project_name'], 'inputfiles', self.config['inputfile']
        )
        return os.path.splitext(fname)[0] + '-{:d}'.format(iterator) + os.path.splitext(fname)[1]

    def get_sh_filename(self, filetype='job'):
        """
        Get the filename of the job.sh file
        :return: The file name
        """
        return os.path.join(
            self.config['output_directory'],
            self.config['project_name'],
            'bash',
            self.config['project_name'] + '.' + filetype + '.sh'
        )

    def _cpu_count(self, max_cpus=None):
        """
        Counts number of CPUs in the system
        :return: number of CPUs available
        """
        if self._local_cpu_count is not None:
            return self._local_cpu_count

        num = 1
        if sys.platform == 'win32':
            try:
                num = int(os.environ['NUMBER_OF_PROCESSORS'])
            except (ValueError, KeyError):
                pass
        elif sys.platform == 'darwin':
            try:
                num = int(os.popen('sysctl -n hw.ncpu').read())
            except ValueError:
                pass
        else:
            try:
                num = os.sysconf('SC_NPROCESSORS_ONLN')
            except (ValueError, OSError, AttributeError):
                pass

        if max_cpus is not None:
            num = min(num, max_cpus)

        self._local_cpu_count = num

        return num

    def validate_config(self):
        """
        Validates parameters of the configuration file. May ask the user for confirmation of some parameters.
        :return: Boolean indicating if cluster jobs can be submitted (True) or submission should be stopped (False).
        """
        def get_max_time_days():
            timesplit = self.config['cluster']['max_time'].split('-')
            if len(timesplit) == 1:
                return 0
            else:
                return int(timesplit[0])

        def get_num_jobs():
            return int(float(self.config['array']['last'] - self.config['array']['first']) /
                       float(self.config['array']['step']))

        # make user confirm priority queue usage
        if self.priority_queue:
            question = 'Warning:\n' \
                       'You are about to use a priority queue. The priority queue is intended for testing ' \
                       'scripts with a run time of several minutes or for urgent computations needed for ' \
                       'publications. Usage of the priority queue must be announced to the slurm mailing list prior ' \
                       'to submission (except for testing purpose). The maximum job time is 1 day. >>> Do you want ' \
                       'to continue?'
            if not parseynanswer(question):
                return False

        # make user confirm jobs with a long maximum runtime
        if get_max_time_days() >= 4:
            question = 'Warning:\n' \
                       'You are about to submit jobs with a maximum run time of {:d} days. Submitting jobs ' \
                       'with a long run time prevents the scheduling system to distribute resources in a fair way ' \
                       'among users, because long-running jobs block cluster nodes. >>> Do you want to ' \
                       'continue?'.format(get_max_time_days())
            if not parseynanswer(question):
                return False

        # make user confirm submission with a large number of jobs
        if get_num_jobs() >= 1000:
            question = 'Warning:\n' \
                       'You are about to submit {:d} jobs. Submitting a large number of jobs slows down the ' \
                       'cluster and does not use resources in an optimal way. >>> Do you want to ' \
                       'continue?'.format(get_num_jobs())
            if not parseynanswer(question):
                return False

        return True


class InteractiveCluster:
    def __init__(self, partition=None, dry=False):
        """
        The constructor of the cluster class takes care of all preparation necessary before connecting in an
        interactive session to the cluster, in particular interactively asking all parameters.
        :param partition: The partition to connect to.
        :param dry: Dry run: just output the correct bash command.
        """
        self.settings = parse_settings()
        self.partition = partition if partition is not None else self.settings['partitions'][-1]['name']
        assert not self.partition == 'local'
        self.dry = dry

        # determine slurm configuration in advance
        self.partition_idx = get_partition_idx(self.settings, self.partition)
        self.slurmconf = self.settings['partitions'][self.partition_idx]['slurmconf']
        if 'job_init_command' in self.settings and self.settings['job_init_command']:
            self.job_init_command = self.settings['job_init_command'] + '; '
        else:
            self.job_init_command = ''

        # get parameters interactively
        self.mem = variableinput('Memory', default='1024M')
        self.mincpus = typedvariableinput('Minimum CPUs', 1, int)
        self.workstation = variableinput('Workstation', default='any')
        self.jobname = 'Interactive session (PyCluster)'

    def run(self):
        command = '{}export SLURM_CONF={};' \
                  'srun -n 1 --pty --x11 --job-name "{}" -p "{}" --mem "{}" --mincpus "{:d}"'.format(
            self.job_init_command, self.slurmconf, self.jobname, self.partition, self.mem, self.mincpus
        )
        if self.workstation != 'any':
            command += ' -w {}'.format(self.workstation)
        command += ' bash'
        subprocess.run(command, shell=True, executable='/bin/bash')
