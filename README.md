# Pycluster
*A python script to efficiently run scripts on a slurm cluster.*

## General usage

The python script `pycluster.py` assumes that one executable (for example a Geant4 simulation, or Python) needs be
executed many times, each time with a different input file. Pycluster will do all the repetitive steps for you like
creating input files and submitting a slurm job array. You will need to define a template for the input files and
the python script will generate copies of it filling placeholders with variables that you can define in a
[JSON](https://en.wikipedia.org/wiki/JSON) configuration file.

Run the following code to create a JSON file for a cluster run with variables following the Python-example type:
```shell
pycluster create Python-example
```
The script will ask you values for various variables and in the end will tell you where it created the JSON file. The
most important variables are:
- `array first`: the first job index to be executed (including)
- `array step`: the increment between two job indices
- `array last`: the last job index to be executed (including)
- `partition`: the cluster partition to run at (cluster partitions [need to be configured](#cluster-specific-settings))
- `identifier`: a unique string that identifies this cluster run (so your old data is not overwritten)  

Use the following code to submit the job array to the cluster
```shell
pycluster run /path/to/your-file.cluster.json
```

If the job was submitted successfully it will tell you the job ID and you will see your job array in the cluster queue.
Note, that before calling `pycluster run` you can modify the JSON file to change any variable inside it.

### Examples

In the repository, there are three examples for cluster jobs. The most basic one is a cluster job that calls Python to
calculate the power 3 of a range of numbers. Each job calculates the power and writes the result to a file as well as
to stdout. The same example exists using bash instead of python. Both examples should be executable out of the box.
A third example is an example to run a Geant4 simulation with a generated mac file. This example needs to be modified
before it can be run. 

## Installation

### Get the code

Clone the repository to a directory of your choice. In all examples you will need to replace `/path/to/directory` with
the directory you chose.
```shell
cd /path/to/directory
git clone https://github.com/jannisdickmann/pycluster.git
cd pycluster
```

### Install dependencies

The cluster script only runs with Python 3 and has three dependencies:  `docopt`, `Jinja2` and `MarkupSafe`. These are
listed with their correct version in `requirements.txt`.

It is highly recommended to install dependencies in a virtual environment (or conda environment). The following lines
create a new environment called `pycluster` and install the dependencies automatically.
```shell
cd /path/to/directory/pycluster
virtualenv -p python3 ~/.virtualenvs/pycluster
. ~/.virtualenvs/pycluster/bin/activate
pip install -r requirements.txt
deactivate
```

### Make script available under alias

To make the cluster script available at any time you can modify your `.bashrc` file by typing `gedit ~/.bashrc` and then
pasting the following lines at the end of the file. Again, you need to replace the correct path.
```shell
pycluster() {
	. ~/.virtualenvs/pycluster/bin/activate
	python /path/to/directory/pycluster/pycluster.py "$@"
	deactivate
}
```

You can now submit your first cluster script using two commands from the beginning:
```shell
pycluster create Python-example
pycluster run /path/to/your-file.cluster.json
```

## Define your own cluster runs

To define your own cluster runs you need to create two files: a configuration file and a template input file.
The configuration file stores all variables (i.e. the number of jobs or the particle energy of a Monte Carlo
simulation). These variables are then used to generate input files from the template input file using a
[templating system](https://jinja.palletsprojects.com/en/2.10.x/templates/). Each job within the slurm cluster array will then
call an executable (which you can define in the configuration file) and pass each of the input files as an argument.

### Configuration files

Configuration files go into the `/path/to/directory/pycluster/configs/` directory. Copy the `Python-example.json` file and
name it for example `Geant4.json`, if you want to create a cluster run for a Geant4 simulation. In the latter case you
would be able to use `pycluster create Geant4` to create a new cluster run definition. Any configuration file *must*
have the following variables (without them it will fail).
- `cluster`: A dict defining general cluster parameters in three sub-variables:
    - `partition`: The cluster partition for the jobs to be submitted to (cluster partitions [need to be configured](#cluster-specific-settings)), which can be overwritten with the `--partition` option when submitting
    - `max_memory`: Maximum memory to allocate.
    - `max_time`: Maximum time for one job to run.
    - `mail`: Set to `"ALL"` to get status updates by mail
- `executable`: The executable to run (this could be `/usr/bin/python3.5` or your own Geant4 executable)
- `output_directory`: The top directory to write any output to. A subdirectory will be created for every cluster run.
- `project_name`: The name of the subdirectory for output to be written to. This should be used to avoid that output
is unintentionally overwritten. Note, that you can use any outher variable inside double curly braces, e.g.
`{{identifier}}` as a placeholder. Placeholders are only possible in the `project_name` variable.
- `identifier`: A string specific to this cluster run (can be used in `project_name`).
- `array`: A dict defining the following three sub-variables:
    - `first`: index of first submitted job (typically 0)
    - `step`: increment between two job indices
    - `last`: index of last submitted job
- `jobs`: run only specific job indices (e.g. 4,8,20,24-48:4) which are compatible with the definitions in `array`; this
can be overwritten with the `--jobs` option when submitting
- `inputfile`: filename with extension of the template inputfile used (see next section)

Any of these variables can directly be defined with a string (or integer for the `array` variables). Alternatively, you
can set them to `{ "default": "value" }` and they will be interactively filled when invoking the `pycluster create`
command. In this case `"value"` must be replaced by a useful default value.

On top of these variables, you can define any other variable you wish to use later on. If you define them directly, they
can be strings, integers, or even lists. Interactively set variables can only be strings. In the `Python-example.json`
we added the variable `"power": 3`, which you can delete in your configuration.

### Template input files

Template input files go into the `/path/to/directory/pycluster/templates/` directory. They can have any extension and any
content you need to supply to the executable. You can choose any filename for the template input file, but you must
specify this filename in the corresponding configuration file. For every job, the cluster script will generate a copy of
your template file, replace placeholders with the variables provided in the configuration file and call the executable
with the input file as first argument.

In your template file you can use any variable name defined in the configuration file enclosed with double curly braces
as placeholder. For example `{{ output_directory }}` will be replaced by the value defined in the configuration file.
Some variables will be generated dynamically. The most important one is `{{ iterator }}`, which will contain the job
ID and which you will need to use in order to change the computation you are performing on the cluster. Another dynamic
variable is `{{ user }}` which will be replaced by your username. You can use `{{ array.step }}` to get the job ID
increment.

The templating system is more powerful. It can also perform if- and for-statements, which are enclosed in `{% ... %}`.
For example:
```jinja
phantom_name = "{{ phantom }}"
{% if phantom == 'Catphan' %}
phantom_catphan_size = {{ catphan_size }}
{% endif %}
```
If in your configuration you defined `"phantom": "Water"`, this will output:
```python
phantom_name = "Water"
```
If instead you defined `"phantom": "Catphan"` and `"catphan_size": 150`, you will get:
```python
phantom_name = "Catphan"
phantom_catphan_size = 150
```
Moreover, you can use mathematical operations on variables, for example the following will print the value of the size 
variable divided by 25:
```jinja
var = {{ size / 25 }}
```
You can also use other functions (called [filters](https://jinja.palletsprojects.com/en/2.10.x/templates/#filters)) 
using the `|` operator, for example:
```jinja
var = {{ [1, 2, 3] | first }}                          # return the first element of a list
var = {{ 9999 | randomint }}                           # get a random integer from 0 to 9999
var = {{ [9, 99] | randomfloat }}                      # get a random float from 9 to 99
var = {{ '/path/to/file.mha' | filesize }}             # get the filesize in bytes
var = {{ '/path/to/file.mha' | filesize / 1000 }}      # get the filesize in megabytes
var = {{ '/path/to/file.csv' | readtxt }}              # read a txt file into a variable
var = {{ ['/path/to/file.csv, 9] | readtxt }}          # read the 9-th line of a txt file into a variable
```
You can find more examples in the [online documentation](https://jinja.palletsprojects.com/en/2.10.x/templates/).

### The job file
In addition to the templates you created, you will find the file `/path/to/directory/pycluster/templates/job.sh`. This is
used to submit jobs to the cluster. In general, you don't need to modify it, but you may need for more complicated
cases. This is also a template. so you can also use your configuration variables here. But unlike the template input
files, every configuration uses the same job file, so you may need to use if clauses. For example:
```jinja
source /etc/profile.d/modules.sh
{% if inputfile == 'Geant4.mac' %}
module unload clhep
module unload root
module load root/6.12.06
module unload geant4
module load geant4/10.03
{% endif %}
```
In this case example modules are only loaded if the template input file is `Geant4.mac`.

## Useful features
- If you set `"copy_executable": true` in your configuration file, your executable will be copied to your output
directory. This is useful if you compile the executable yourself and you want to avoid that your cluster jobs fail
if you compile again while they run. Also, you have a copy of the executable to reproduce your results.
- If you set `"output_subdirectories": ["a", "b"]`, the directories `a` and `b` will be created under your output
directory to make sure your jobs can write to these.
- You can use `pycluster run <config> --partition <partition>` to run the script on the partition `partition`, 
overwriting what was defined in the configuration file.
- To run only specific jobs (e.g. those that failed during a previous run), use the `--jobs` option: `pycluster run <config> --jobs 1,2,6-10`. The jobs (1, 2, and 6 to 10) must be compatible with the definition of `array` in the json file.

## Cluster-specific settings
PyCluster needs to know basic information on your slurm configuration in `settings.json`. For each partition,
the name of the queue, and the path to the slurm configuration need to be given. It also needs to be indicated
if this is a queue with high priority.
