#########################################################################################################
# Calculate the power {{power}} of the number {{iterator}} and write result to disk.
#########################################################################################################

# {{iterator}} and {{power}} will be replaced by pycluster.py
number={{iterator}}  # in example: iterator will be 0, 4, ..., 356
power={{power}}
echo "We are calculating the power ${power} of ${number}."
powerofnumber=$((${number}**${power}))
echo "The power ${power} of ${number} is ${powerofnumber}."

# finally write the result to disk {{output_directory}} will be replaced by pycluster.py
outputdir="{{output_directory}}/{{project_name}}/output"
mkdir -p ${outputdir}
fname="${outputdir}/output-${number}.txt"
echo "The power ${power} of ${number} is ${powerofnumber}." >> ${fname}