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
| cloudLock     | boolean           | No        | F | Prevent cloud resources (e.g. AWS, GCloud) from being used to run this task


#### requirements

| Key           | Value(s)          | Required  |Out| Notes                         | 
| --------------|-------------------|-----------|---|-------------------------------|

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

Finally you will notice the base command `env`. Again, since the `manageSys` is defaulting to localhost
the 

##### ???