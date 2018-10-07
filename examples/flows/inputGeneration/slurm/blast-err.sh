#!/usr/bin/env bash

BLAST_CH=/var/tmp/blast
BLAST_OUT=output

ch-run --no-home -b ${BLAST_OUT} ${BLAST_CH} -- sh -c "cat /mnt/0/input.fasta.0.err \
    /mnt/0/input.fasta.1.err > /mnt/0/output.fasta.err"