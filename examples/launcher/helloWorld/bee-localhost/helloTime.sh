#!/usr/bin/env bash

file=/var/tmp/hello.test

touch $file
echo "Hello, world! The time is $(date)." >> $file
echo $file " has bee updated!"