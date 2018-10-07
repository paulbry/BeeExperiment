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

i=0
while [ ${i} -le ${NUM} ]
do
   touch ${BLAST_OUT}/input.fasta.${i}.err
   ((i++))
done