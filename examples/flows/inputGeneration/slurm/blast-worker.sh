#!/usr/bin/env bash

BLAST_CH=/var/tmp/blast
BLAST_LOC=/home/beeuser/makeflow-examples/blast
BLAST_OUT=output

while getopts n: option
    do
        case "${option}" in
            n) NUM=${OPTARG};;
        esac
done

ch-run --no-home -b $BLAST_OUT $BLAST_CH -- sh -c "$BLAST_LOC/blastall -p blastn \
	-d $BLAST_LOC/nt/nt -i /mnt/0/small.fasta.$NUM -o /mnt/0/input.fasta.$NUM.out \
	2> /mnt/0/input.fasta.$NUM.err"