#!/bin/bash

BLAST_OUT=output

rm -rf ${BLAST_OUT}
mkdir ${BLAST_OUT}

# Create error files (empty)
touch ${BLAST_OUT}/input.fasta.0.err \
        ${BLAST_OUT}/input.fasta.1.err \
        ${BLAST_OUT}/output.fasta.err