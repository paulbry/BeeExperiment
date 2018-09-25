### Composing your Beefile
The `beefile` is a core concept in Bee workflow engine as it contains all required logic for any task you choose 
to invoke. In the original implementation of [Bee](https://github.com/lanl/BEE) you may notice that the file is 
organized via the json standard; however, I have chosen to implement it using [YAML](http://yaml.org/). This 
is partly because of my desire to make use of some of the exicting concepts found in the 
[Common Workflow Language](http://www.commonwl.org/user_guide/license/) and to draw simulates between other
tools being utilized in this space.

It is important to note that if you have familiarity with Common Workflow Language (CWL) that may not 
offer more than a passing benefit here. Though there are some similarities in the terminology/structures to CWL, 
BeeExperiment is not compliant with that standard at this time. As such I have tried my best to document
the current implementation of `beefile` functionality in this BeeExperiment. Please also refer to the 
additional examples I have included in the project for more details.


| Key           | Value(s)          | Required  |Out| Notes                         | 
| --------------|-------------------|-----------|---|-------------------------------|
| id            | string            | Yes       | F | Identification for task, keep unique during workflow to assist identification.
| label         | string            | No        | F | Description of the task
| requirements  | *see below*       | Yes       | * | All requirements that apply to establishing an allocation
| inputs        | *see below*       | No        | * | Input parameters that can be utilized through the process
| workerBees    | *see below*       | No        | * | Specified actions preforms within the allocation, executed by the `Bee-Orchestrator`
| terminateAfter| boolean           | No        | * | Terminate the `Bee-Orchestrator` along with the associated allocation upon completion of the task. Default behavior = `true`
| baseCommand   | string            | No        | T | Command/program to be invoked, see the **inputs** section for details how flags/options are applied.
| cloudLock     | boolean           | No        | F | Prevent cloud resources (e.g. AWS, GCloud) from being used to run this task. Default behavior = `false`
| monitored     | boolean           | No        | F | Prevent all monitoring of any `Bee-Launcher` and `Bee-Orchestrator` events via the `Bee-Monitor` module if this is set to `false`. Default behavior = `true`

```yaml
id: <string>
label: <string>
requirements:
    <...>
inputs:
    <...>
workerBees:
    <...>
terminateAfter: <boolean>
baseCommand: <string>
cloudLock: <boolean>
monitored: <boolean>
```

#### requirements
All `requirements` defined relate to execution environment that the `Bee-Orchestrator` will  run in. In the HPC space 
this would be the allocation (obtained, for instance, via `salloc`). Key/values found in the `requirements` section
are focused on ensuring that first and foremost you obtain an allocation that meets your workflow's needs but also 
that software/environmental requirements are account for.

All requirements will be fulfilled prior to any defined tasks (`workerBees` or `baseCommand`) being execute. However,
it is important to note that some requirements defined may not be meet on all possible platforms **if** specific 
criteria isn't first met. As the `requirements` are documented this will be explained further.

| Key           | Value(s)          | Required  |Out| Notes                         | 
| --------------|-------------------|-----------|---|-------------------------------|
| ResourceRequirements | *see below* | No       | * | 
| SoftwareModules   | *see below*   | No        | * |
| EnvVarRequirements | *see below*   | No        | * |
| CharliecloudRequirement   | *see below*   | No | * | 

```yaml
requirements:
    ResourceRequirement:
      <...>
    SoftwareModules:
      <...>
    CharliecloudRequirement:
      <...>
    EnvVarRequirements:
      <...>
```
##### ResourceRequirements
Resources such as the number of nodes or maximum job time that will be used when allocating hardware resources
for the purposes of fulfilling the task(s) defined.

| Key           | Value(s)          | Required  |Out| Notes                         | 
| --------------|-------------------|-----------|---|-------------------------------|
| numNodes      | int               | Yes*      | F | The number of nodes/computer you are requesting in the allocation.
| nodeList      | string            | No*       | F | Sepcific nodeList (e.g. hosts) that will be used for the defined task in the allocation. Will be automatically populated as port of an `Internal BeeFlow`
| jobTime       | string            | No*       | F | Maximum time the task can run for. Format as such: `"hh:mm:ss"`
| partition     | string            | No        | F |
| manageSys     | system            | Yes    | F | The mangement system (e.g. resource job management system) used for the purpose of allocation and ppossibly execution. At this time only `slurm` and `localhost` are defined.
| custom        | {key: value}, string | No*    | F | User defined flags that will be used as part of the allocation script. For example, `#SBATCH key value` or `#SBATCH string` 

* (*) For `localhost` allocations the requirements defined here cannot be realized.

```yaml
numNodes: <int>
nodeList: <string>
jobTime: <string>
partition: <string>
manageSys: <system>
custom:
    <key>: <value>
    <string>
```

##### SoftwareModules
Take advantage of [Environmental Modules](https://modules.readthedocs.io/en/stable/index.html) by running `modules load moduleName` 
or when specified `module load moduleName/version`

| Key           | Value(s)          | Required  |Out| Notes                         | 
| --------------|-------------------|-----------|---|-------------------------------|
| moduleName    | string (unique)   | No        |   | The name of the modules you wish to load
| version       | string            | No        | F | Version, will be appended after `modulename/`

It is a requirement that when utilized the environment has already been supplied the correct software both for `module` 
as well as anything the user wishes to load. Bee will not check for these requirements and could have unexpected results 
if modules are missing or load incorrect versions.

```yaml
moduleName1:
moduleName2:
    version: <string>
```

##### CharliecloudRequirement
[Charliecloud](https://github.com/hpc/charliecloud) provides user-defined software stacks, similar to Docker, with the 
benefit that it does not require elevated user privilege or a daemon.  

| Key           | Value(s)          | Required  |Out| Notes                         | 
| --------------|-------------------|-----------|---|-------------------------------|

```yaml

```

##### EnvVarRequirements

| Key           | Value(s)          | Required  |Out| Notes                         | 
| --------------|-------------------|-----------|---|-------------------------------|

````yaml

````

#### inputs

The `inputs` section is associated first and foremost with identifying user defined variables and where appropriate
assigning them a default value. Additionally these variables can be bound to specific `position` and potentially with
specified `prefix` to the base command. For instance, `<baseCommand> <input_prefix> <input_value>`

```yaml
inputs:
  variableID:
    type: <type>
    inputBinding:
      position: <position>
      prefix: <prefix>
    default: <default>
```

| Key           | Value(s)          | Required  |Out| Notes                         | 
| --------------|-------------------|-----------|---|-------------------------------|
| variableID   | type, inputBinding, default                  | Yes       | F | Unique name used to identify the variable through the workflow and link it to any user supplied `input.yml`.
| type          | string            | Yes       | F | Expected data type of variable, currently  `file`, `string`, `int,` and `boolean` are supported.
| inputBinding  | position, prefix                  | No        | * | Key for dictionary that contextualizes the inputs to be used with the base command.
| position      | int               | Yes       | N | Position (assuming `baseCommand` is 0) in the invocation.
| prefix        | string            | No        | N | Any type of flag/option that should appear prior to the binding.
| default       | ?                 | No        | Y | Default value that will be assigned to the variable. Will be overwritten by any user supplied input.

#### workerBees

| Key           | Value(s)          | Required  |Out| Notes                         | 
| --------------|-------------------|-----------|---|-------------------------------|
| 

#### Examples
##### Basic
```yaml
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
      - sh:
          flags:
            - helloTime.sh
terminateAfter: true
baseCommand: env
```

In this example you will that the `manageSys` is not included, as such BEE will be 
defaulting to localhost. This means a bash script will be generated that, inside a screen, sets:

    -  `PATH=$HOME/.local/bin:$PATH`
    -  `source activate bxp`
    
After-which the `Bee-Orchestrator` will be launched. In turn this will:
1. `$ sh helloTime.sh` -> Invoked the script helloTime
2. `$ env` -> Print environment variables

##### ???