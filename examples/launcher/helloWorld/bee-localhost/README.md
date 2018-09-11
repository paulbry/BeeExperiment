Simple example that will run exclusively via your host machine. Before running insure that you have meet all BEE requirements that are defined in the documentation.

Take a moment prior to launching to verify the `EnvVarRequirements:`. In this example we have defined several keys that may not be required for your environment.
* `envDef: ...`
        -> `export PATH=$HOME/.local/bin:$PATH`
* `sourceDef: ..`
        -> `source activate beeenv` 
       
Launch: `bee-launcher -l helloWorld`

Keep in mind that the launcher will first build a script that will be invoked within a `screen`. This scripts will establish the environment as defined under `requirements:` followed by initating the `Bee-Orchestrator`.