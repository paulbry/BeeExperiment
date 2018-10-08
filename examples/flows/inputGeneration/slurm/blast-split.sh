#!/usr/bin/env bash

BLAST_CH=/var/tmp/blast
BLAST_LOC=/home/beeuser/makeflow-examples/blast
BLAST_OUT=output
NUM=5

ch-run --no-home -b ${BLAST_OUT} -c ${BLAST_LOC} ${BLAST_CH} -w -- sh -c "./makeflow_blast -d nt -i small.fasta \
                            -o output.fasta -p blastn --num_seq $NUM --makeflow blast.mf && \
                            ./split_fasta $NUM small.fasta"

ch-run --no-home -b ${BLAST_OUT} -c ${BLAST_LOC} ${BLAST_CH} -- sh -c "cp small.fasta.* /mnt/0"