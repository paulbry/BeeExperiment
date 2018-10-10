This example will be using the LAMMPS general example (https://github.com/paulbry/BeeExperiment/tree/master/examples/bee-og/lammps/slurm/general).

## Prepartion

```yaml
id: lammpsExample
label: LAMMPS example from https://github.com/lanl/BEE
requirements:
  ResourceRequirement:
    manageSys: slurm
    numNodes: 1
    jobTime: "00:30:00"
  SoftwareModules:
    friendly-testing:
    charliecloud:
    python:
      version: 3.6-anaconda-5.0.1
    openmpi:
      version: 1.10.5
  EnvVarRequirements:
    envDef:
    - PATH: $HOME/.local/bin
    sourceDef:
    - activate: bxp
  CharliecloudRequirement:
    lammps:
      source: /usr/projects/beedev/lammps/mpi_1.10/lammps.tar.gz
      tarDir: /var/tmp
      removeAfter: true
      defaultFlags:
        - -b: output
workerBees:
  - Command:
      - mkdir:
          cmd: ['mkdir', '-p', 'output']
  - Task:
    - /lammps/src/lmp_mpi:
        container:
          name: lammps
        flags:
          - -in: /lammps/examples/melt/in.melt
          - -log: /mnt/0/lammps_gen.log
terminateAfter: true
```

## Launch

## Allocate

## Execute

## Monitr
