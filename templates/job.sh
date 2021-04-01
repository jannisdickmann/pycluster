#!/bin/bash

########################################################################
# Cluster Settings

#SBATCH --job-name='{{project_name}} (PyCluster)'
#SBATCH --output={{output_directory}}/{{project_name}}/log/{{project_name}}_%a.log
#SBATCH --error={{output_directory}}/{{project_name}}/err/{{project_name}}_%a.err
#SBATCH --mincpus=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu={{cluster.max_memory}}
#SBATCH --partition={{cluster.partition}}
#SBATCH --mail-type={{cluster.mail}}
# #SBATCH --mail-user={{user}}@domain.com # change to correct email and remove # in the beginning to receive email notifications
#SBATCH --time={{cluster.max_time}}

echo "Job number ${SLURM_ARRAY_TASK_ID}"
then=$(date +'%Y-%m-%d %T')
echo "Starting job at ${then}."

{% if 'Geant4-example.mac' == inputfile %}
source /etc/profile.d/modules.sh
module unload clhep
module unload root
module load root/6.12.06
module unload geant4
module load geant4/10.03
{% endif %}

# Run executable with input file
"{{executable}}" "{{output_directory}}/{{project_name}}/inputfiles/{{ inputfile | splitext | first }}-${SLURM_ARRAY_TASK_ID}{{ inputfile | splitext | last }}"

echo "Started job at ${then}."
now=$(date +'%Y-%m-%d %T')
echo "Finished job at ${now}."
