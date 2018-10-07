#!/usr/bin/env bash

BLAST_CH=/var/tmp/blast
BLAST_LOC=/home/beeuser/makeflow-examples/blast
BLAST_OUT=output

ch-run --no-home -b ${BLAST_OUT} ${BLAST_CH} -- sh -c "cp $BLAST_LOC/small.fasta /mnt/0 && \
                                $BLAST_LOC/split_fasta 500 /mnt/0/small.fasta"