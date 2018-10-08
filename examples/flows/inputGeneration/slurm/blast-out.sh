#!/bin/bash

BLAST_OUT=output

rm -rf ${BLAST_OUT}
mkdir ${BLAST_OUT}


while getopts n: option
    do
        case "${option}" in
            n) NUM=${OPTARG};;
        esac
done

# Create error files (empty)
touch ${BLAST_OUT}/output.fasta.err

cmd="/home/beeuser/makeflow-examples/blast/cat_blast /mnt/0/output.fasta"

i=0
while [ ${i} -le ${NUM} ]
do
   cmd="$cmd /mnt/0/input.fasta.$i.out"
   ((i++))
done

ch-run --no-home -b output /var/tmp/blast -- ${cmd}
