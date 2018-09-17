#!/bin/bash
# parallel run of lammps for BEE Charliecloud launcher

ch-run \
 -b output \
 /var/tmp/lammps \
 -- /lammps/src/lmp_mpi \
 -in /lammps/examples/melt/in.melt -log /mnt/0/lammps_mpi_1.log # has larger region 50 steps