#!/usr/bin/env bash
# /var/tmp/hello.test

while getopts f: option
    do
        case "${option}" in
            f) LOCATION=${OPTARG};;
        esac
    done

rm -f ${LOCATION}
touch ${LOCATION}
echo "Hello, world! The time is $(date)."