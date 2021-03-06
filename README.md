[![Build Status](https://travis-ci.com/paulbry/BeeExperiment.svg?branch=master)](https://travis-ci.com/paulbry/BeeExperiment)
[![Coverage Status](https://coveralls.io/repos/github/paulbry/BeeExperiment/badge.svg?branch=master)](https://coveralls.io/github/paulbry/BeeExperiment?branch=master)

# BeeExperiment
BeeExperiment is a drastic rewrite of the original open project in an effort to explore
new ideas, highlight possible changes, and act as an educational endeavor. Some of the 
goals undertaken were:

•	Individually package and logically separate Bee-Launcher from Bee-Orchestrator.

•	Construct and implement a new architecture to support targeting a variety of management systems while ensuring that the core functionality remains consistent.

•	Propose a standardized algorithm in conjunction with a new class structure.s.

•	Re-engineer BeeFlow while keeping the core concepts found intact.

•	Greatly expand the structure of both the beefile in addition to beeflow file.

•	Introduce structure for supporting Bee-Monitor and Bee-Logging through improved status tracking.
 

**IMPORTANT** This project features on going work, epically with regards to
incorporating better documentation. In addition I have identified a few bugs
and will going forward (due to the switch from private -> public repo) attempt 
to be more proactive about documenting these.


# Deployment Instructions

### Requirements
- Linux
- Bash
- Screen
- Charliecloud (recommended)
- Anaconda (recommended)

```bash
$ conda create -n bxp python=3.6 python
$ source activate bxp
$ git clone https://github.com/paulbry/beeexperiment
$ cd BeeExperiment/src
$ pip install . ---user
$ export PATH=$HOME/.local/bin:$PATH
```

# From 0 to Experiment

1. Create the following `hello.beefile`, note that is assumes the use of a Anaconda
environment name `bxp` (`conda -n <name>`)
    
    ````yaml
    id: helloWorld
    label: Basic hello world example
    requirements:
        EnvVarRequirements:
          envDef:
            - PATH: $HOME/.local/bin
          sourceDef:
            - activate: bxp
    workerBees:
        - Task:
          - touch:
              flags:
                - randomFile.txt
    terminateAfter: true
    baseCommand: env
    ````

2. Verify `source activate bxp`.

3. `bee-launcher -l hello.beffile` will launch workflow in a screen

4. `bee-orchestrator --orc -t hello` will allow you to see the launch

# Copyright
TODO


### NOTES
This work is derived from [BEE: Build and Executed](https://github.com/lanl/BEE)

In addition attributes from the [Common Workflow Language](https://www.commonwl.org/) and
 [Software Carpentry](https://software-carpentry.org/) but is not nearly CWL compliment at this 
 time.
