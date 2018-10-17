#!/bin/bash

BLAST_OUT=output
BLAST_CH=/var/tmp/blast
BLAST_LOC=/home/beeuser/makeflow-examples/blast

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

i=0
while [ ${i} -le ${NUM} ]
do
   touch ${BLAST_OUT}/input.fasta.${i}.err
   ch-run   --no-home -b ${BLAST_OUT} -c ${BLAST_LOC} ${BLAST_CH} -- \
            sh -c "cp small.fasta.${i} /mnt/0"
   ((i++))
done