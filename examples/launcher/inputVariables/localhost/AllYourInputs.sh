#!/usr/bin/env bash

while getopts f:i:l: option
    do
        case "${option}" in
            f) LOCATION=${OPTARG};;
            i) INPUT=${OPTARG};;
            l) LOOPS=${OPTARG};;
        esac
    done

for (( j=1; j<=${LOOPS}; j++))
	do
		echo ${j} "- " ${INPUT} >> ${LOCATION}
	done