#!/bin/bash

jobfile="{{output_directory}}/{{project_name}}/bash/{{project_name}}.job.sh"
tasksparallel={{cores_local}}
arrayfirst={{array.first}}
arraystep={{array.step}}
arraylast={{array.last}}

echo "   🚀   Started running jobs form index {{array.first}} to index {{array.last}} in steps of {{array.step}}. Running {{cores_local}} jobs in parallel."

for i in $(seq ${arrayfirst} ${arraystep} ${arraylast});
do
	if [[ $((i % (tasksparallel*arraystep))) = 0 ]]; then
		wait
		if [[ ${i} -gt 0 ]]; then
      echo "   🏁   Done running the above jobs."
    fi
	fi
	(
    logfile="{{output_directory}}/{{project_name}}/log/{{project_name}}_${i}.log"
    errfile="{{output_directory}}/{{project_name}}/err/{{project_name}}_${i}.err"
		echo "   🏃   Running job with index ${i}."
		SLURM_ARRAY_TASK_ID=${i}
		source "${jobfile}" 1> "${logfile}" 2> "${errfile}"
	) &
done

wait
