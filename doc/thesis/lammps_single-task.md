This example will be using the [LAMMPS general example](https://github.com/paulbry/BeeExperiment/tree/master/examples/bee-og/lammps/slurm/general).
In addition please insure that you can install BEE in addition to the following:
- Slurm
- Charliecloud

## Preparation 

Began process by installing the `Bee-Experiment` package on the target environment. This insure
 it is available on both the login node as well as any compute nodes in the allocation.
 In the example I'm using a Anaconda environment (named `bxp`).

```bash
(bxp) $ git clone https://github.com/paulbry/BeeExperiment.git
(bxp) $ cd BeeExperiment/src
(bxp) $ pip install . --user
```

At this time the `Bee-Experiment` package is not stored on the Python Package Index (PyPI) and 
as such you will need to use the above method. Next the `beefile` needs to be created.
Below is the file this example utilizes. Key components regarding the allocation you should note:
- `slurm` is the defined management system
- Will load 4 software modules (`module load ...`)
- The `EnvVarRequirements` are being used to insure that the Anaconda environment is activated.
- The `lammps` Charliecloud container will be loaded

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

Finally, due to some limitations in Bee there is no standardized method for supporting a
container's build process. As such the following steps are assumed to have occcured
on a separate machines in order to have the LAMMPS container ready (https://hub.docker.com/r/beelanl/cc-lammps/).

```bash
$ docker pull beelanl/cc-lammps
$ ch-docker2tar beelanl/cc-lammps /var/tmp/lammps.tar.gz
$ scp /var/tmp/lammps.tar.gz <SYSTEM>:usr/projects/beedev/lammps/mpi_1.10/
```

## Launch

Launching the allocation occurs via user interaction via the target cluster's login node. For the purpose of 
examining BeeExperiment we are assuming that the login nodes is always available. If not, even
standard methods (scripts/manual/BEE) would be unavailable.

```bash
$ source activate bxp
(bxp) $ bee-launcher -l lammps_cc_gen.beefile
```

Now `bee-launcer` has been invoked via command line we are accessing the `bee_launcher` module.
This module has a `__main__.py` python file that defines the logic related to argument parsing 
via the `argparse` (https://docs.python.org/3.6/library/argparse.html). In turn the argument 
(`-l lammps_cc_gen.beefile`) is identified and `-l` relates to the `bee_launch.py` file,
speifically the `BeeArguments` class (derived from `BeeLauncher`).

From this point `BeeExperiment` will show its first major architectural differentce from BEE
(outside of the obvious changes to the beefile). The `-l` is identified and as such the
`launch()` method is invoked. The `manageSys`, in this case `slurm` is identifed and as such 
the appropriate methods (`specific_allocate` from `tar_slurm.py` found in the 
`bee_internal` module) will be used.

## Allocate

From this point the allocation logic, defined specifically for the appropriate management 
systems. For the purposes of the thesis case studies this will only be for Slurm. As such
the allocation will be focused on leveraging the `sbatch` program. To begin the process 
`BeeExperiment` will identify the user specified task, beefile, and the target management 
system (occurring within `class BeeLauncher`).

```bash
[lammps_cc_gen] Preparing to launch...
        ManageSys: slurm
        Task: lammps_cc_gen
```

From this point an adapter object will be created via the logic found within the 
`launcher_translator.py` and the specific implantation found in the `tar_slurm.py`
file (in the `bee_internal` module). In particular we are interested in the 
`specific_allocate()` method.

During allocation, regardless of the management system we are targeting Linux 
systems (requirement of BEE). As such there are some similarities between the 
adapters and we are able to leverage `shared_tools.py` found within the
`bee_interal` module. I'm not going to go into great detail here on this.

The allocation focuses on building a script that will be submitted to `sbatch`.
This will change depending on the management system and other times more
advanced logic will be required on behalf of `BeeExperiement` to full fill 
the user's defined logic.

1. Resource Requirements
2. Software Modules
3. Environmental Variables
4. Charliecloud

```bash
[lammps_cc_gen] SBATCH CONTENTS
#!/bin/bash
```

##### Resource Requirements
Begin by create a temporary file with a random name. It should be noted that `sbatch`
only requires the file up until it has received and acknowledged the job. This means 
so long as `BeeExperiemnt` waits until it has received an exit status from the request
no file needs to be kept.

```bash
#SBATCH --nodes=1
#SBATCH --time=00:30:00
#SBATCH --job-name=lammpsExample
```

All details associated with the resource requirements as tied to the approaite
`#SBATCH` flag. In additon, I have included a `flags:` key in the design. This 
will allow for users to create their own key/value combinations (`#SBATCH --key=value`)

##### Software Modules
Load software modules for the compute environment.
```bash
# Load Modules
module load friendly-testing
module load charliecloud
module load python/3.6-anaconda-5.0.1
module load openmpi/1.10.5
```

##### Environment Variables
Set environment variable `export <key> <value>:$<key>` or activate sources. In this example 
we are only activate an anaconda environment.

```bash
# Environmental Requirements
source activate bxp
```

##### Charliecloud
The defined Charliecloud container can then be unpacked across the allocation. This is 
also done via scripting, using the `srun` application to insure all nodes have been
accounted for.

```bash
# Deploy Charliecloud Containers
srun ch-tar2dir /usr/projects/beedev/lammps/mpi_1.10/lammps.tar.gz /var/tmp
```

In the future I will need to return to this for two main reasons. Firstly, add support for 
additional container technologies (e.g. Shifter). Secondly there needs to be a 
method for accounting for the size of the allocation and making logical decisions
as to the method to unpack and deploy containers. This is a larger issues, especially
at exascale.

Finally after all requirements from the `beefile` have been included in the launch script
one additional piece of logic is added to insure that `bee-orchestrator` is
invoked with the correct information from with the allocation.

```bash
# Launch BEE
cd /turquoise/users/pbryant/BeeExperiment/examples/bee-og/lammps/slurm/general
bee-orchestrator --orc  -t lammps_cc_gen
```

The script is then sent to the `sbatch` program where we rely on its logic. In addition to the 
information presented to the user via a terminal, the details are stored in `BeeExperiment's`
launch database.

```bash
[lammps_cc_gen] Executing: sbatch /tmp/tmpscr08hqy
[lammps_cc_gen] Launched with job id: 304023
```

## Execute
If we examine the allocation at this point in time we can clearly see the request modules and proper conda environment 
have been loaded. Later  is more so important to how I have choosen to deploy `BeeExperiment` in these examples.

```bash
(bxp) $ module list

Currently Loaded Modules:
  1) python/3.6-anaconda-5.0.1   2) friendly-testing   3) charliecloud/0.9.3   4) openmpi/1.10.5

(bxp) $ conda list
# packages in environment at /usr/projects/beedev/conda/bxp:
#
ca-certificates           2018.03.07                    0
certifi                   2018.8.24                py37_1
cython                    0.28.5           py37hf484d3e_0    anaconda
libedit                   3.1.20170329         h6b74fdf_2
libffi                    3.2.1                hd88cf55_4
libgcc-ng                 8.2.0                hdf63c60_1
libstdcxx-ng              8.2.0                hdf63c60_1
ncurses                   6.1                  hf484d3e_0
openssl                   1.0.2p               h14c3975_0
pip                       10.0.1                   py37_0
python                    3.7.0                hc3d631a_0
readline                  7.0                  h7b6447c_5
setuptools                40.2.0                   py37_0
sqlite                    3.25.2               h7b6447c_0
tk                        8.6.8                hbc83047_0
wheel                     0.31.1                   py37_0
xz                        5.2.4                h14c3975_4
zlib                      1.2.11               ha838bed_2
```

As defined in the allocation step the orchestrator launch upon the successful completion of all other requirements.
`$ bee-orchestrator --orc  -t lammps_cc_gen` This process starts with the orchestrator (using the Pyro4 module) to start
an unprivileged daemon and immediately trigger the launch of the task `lammps_cc_gen`.

```bash
Not starting broadcast server for localhost.
NS running on localhost:38861 (127.0.0.1)
URI = PYRO:Pyro.NameServer@localhost:38861
Starting Bee orchestration controller..
PYRO:obj_c17ac0c9d493404b8ebd54e799fa3412@localhost:41467
Bee orchestration controller started.
[lammps_cc_gen.beefile] Task received in current working directory: /turquoise/users/pbryant/BeeExperiment/examples/bee-og/lammps/slurm/general
Bee orchestration controller: received task creating request
```

Upon competition of this execution phase the `specific_shutdown()` method will be called
from within the allocation. For Slurm this is a simple process; however, it may be more
involved with any future implementation. In the case of Slurm the only part that matters
is all user running processes are completed, and in the case of `BeeExperiment` this 
means that 

## Monitor
It is important to note that `BeeExperiment` takes no responsibility for the user's
results until they choose to invoke `workerBees` upon those tasks. In that case it 
will simply follow the logic established in the `beefile`. This is a choice in the design
as I do not want to guess at how the user wants their results handled. As such it 
is up to them to check or establish a notification process (available via email in Slurm).

```bash
$ cd output/
$ ls -l
total 4
-rw-rw-r-- 1 pbryant pbryant 2810 Oct 16 09:59 lammps_gen.log
```

`BeeExperiment` does however, look after the results of it's own actions in a few
very specific way. Firstly, during the launch/allocation steps listed above all
key details are stored in a launch database (`~/.bee/launch.db`). This is more
important and referenced when dealing with workflow external to the allocation
but can still provide insight.

There is also tracking of `BeeExperiment` actions from within the allocation,
these are stored in `/var/tmp/orc.db` (need to establish framework for overriding
this). Again, I take no responsibility for peering into the applications themselves,
only in the actions of `BeeExperiment` has taken to execute these. 

In both cases the database is still in its early stages. The main idea is highlight
some possible uses and lay the ground work for more serious implementation efforts
down the road. It is also important to note here that all console messages generated
by `BeeExperiemnet` as sent through a sort of decorator object (`bee_logging`). At
this time it is simply for controlling these messages via the user flags (`--log-flag ...
-quite ...`) but could be improved. 

##### Monitor Launch
Can be seen via: `bee-monitor launch -j 304023`

```bash
Beefile Name: None
JobID: 304023
Management System: slurm
Status: Launched
TimeStamp: 2018-10-16 16:01:09
Beefile
        id: lammpsExample
        label: LAMMPS example from https://github.com/lanl/BEE
        requirements:
                ResourceRequirement:
                        manageSys: slurm
                        numNodes: 1
                        jobTime: 00:30:00
                SoftwareModules:
                        friendly-testing: None
                        charliecloud: None
                        python:
                                version: 3.6-anaconda-5.0.1
                        openmpi:
                                version: 1.10.5
                EnvVarRequirements:
                        envDef
                        PATH: $HOME/.local/bin
                        sourceDef
                        activate: bxp
                CharliecloudRequirement:
                        lammps:
                                source: /usr/projects/beedev/lammps/mpi_1.10/lammps.tar.gz
                                tarDir: /var/tmp
                                removeAfter: True
                                defaultFlags
                                -b: output
        workerBees
        Command
        mkdir:
                cmd
                mkdir
                -p
                output
        Task
        /lammps/src/lmp_mpi:
                container:
                        name: lammps
                flags
                -in: /lammps/examples/melt/in.melt
                -log: /mnt/0/lammps_gen.log
        terminateAfter: True
Error: None
```

##### Monitor Orchestrator
Can be seen within the allocation: `bee-monitor orc -a`
```bash
Command: None
TaskID: lammpsExample
JobID: 304022
Status: 20
event: Status change
timeStamp: 2018-10-16 15:58:59

Command: None
TaskID: lammpsExample
JobID: 304022
Status: 40
event: Status change
timeStamp: 2018-10-16 15:58:59

Command: None
TaskID: lammpsExample
JobID: 304022
Status: 50
event: Status change
timeStamp: 2018-10-16 15:58:59

Command: mkdir -p output
TaskID: lammpsExample
JobID: 304022
Status: 50
stdOut: No output captured
exitStatus: 0
event: Subprocess
timeStamp: 2018-10-16 15:58:59

Command: ch-run -b output /var/tmp/lammps -- /lammps/src/lmp_mpi -in /lammps/examples/melt/in.melt -log /mnt/0/lammps_gen.log
TaskID: lammpsExample
JobID: 304022
Status: 50
stdOut: No output captured
exitStatus: 0
event: Subprocess
timeStamp: 2018-10-16 15:59:00

Command: None
TaskID: lammpsExample
JobID: 304022
Status: 60
event: Status change
timeStamp: 2018-10-16 15:59:00

Command: None
TaskID: lammpsExample
JobID: 304022
Status: 70
event: Status change
timeStamp: 2018-10-16 15:59:00
```