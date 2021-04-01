"""
Calculate the power {{power}} of the number {{iterator}} and write result to disk.
"""
import os

# {{iterator}} and {{power}} will be replaced by pycluster.py
number = {{iterator}}  # in example: iterator will be 0, 4, ..., 356
power = {{power}}
print('We are calculating the power {:d} of {:d}.'.format(power, number))
powerofnumber = number**power
print('The power {:d} of {:d} is {:d}'.format(power, number, powerofnumber))

# finally write the result to disk {{output_directory}} will be replaced by pycluster.py
outputdir = '{{output_directory}}/{{project_name}}/output'
os.makedirs(outputdir, exist_ok=True)
fname = outputdir + '/output-{:d}.txt'.format(number)
with open(fname, 'w') as file:
    file.write('Result: the power {:d} of {:d} is {:d}.'.format(power, number, powerofnumber))
