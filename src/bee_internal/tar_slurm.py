# system
from tempfile import NamedTemporaryFile
# project
from bee_internal.shared_tools import TranslatorMethods
from bee_internal.in_out_manage import InputManagement


class SlurmAdaptee:
    def __init__(self, config, file_loc, task_name, beelog, yml_in_file):
        self._config = config
        if self._config is not None:
            self._config_req = self._config.get('requirements')
        self._file_loc = file_loc
        self._task_name = task_name
        self._encode = 'UTF-8'

        # Logging conf. object -> BeeLogging(log, log_dest, quite)
        self.blog = beelog

        # User input via yml
        self._user_values = yml_in_file
        self._beefile_input = self._config.get('inputs')
        self.in_mng = None
        if self._user_values is not None and self._beefile_input is not None:
            self.in_mng = InputManagement(self._beefile_input, self._user_values,
                                          self.blog)

        # Shared tools
        self._stm = TranslatorMethods(config=self._config,
                                      file_loc=self._file_loc,
                                      task_name=self._task_name,
                                      beelog=self.blog)

    def specific_allocate(self, test_only=False):
        """
        Create sbatch file utilizing Beefile's defined 'requirements' then
        execute this sbatch via subprocess.
        At this moment this system must be run on the login node of the cluster
        :return: unique job id associated with successful allocation
        """
        tmp_f = NamedTemporaryFile()
        tmp_f.write(bytes("#!/bin/bash\n\n", 'UTF-8'))
        #######################################################################
        # Prepare SBATCH file
        # TODO: further document
        #######################################################################
        if self._config_req is not None:
            if self._config_req.get('ResourceRequirement') is not None:
                self.__resource_requirement(temp_file=tmp_f)
            else:
                self.blog.message("ResourceRequirement key is required for "
                                  "allocation", self._task_name, self.blog.err)
            if self._config_req.get('SoftwareModules') is not None:
                self._stm.software_modules(temp_file=tmp_f)
            if self._config_req.get('EnvVarRequirements') is not None:
                self._stm.env_variables(temp_file=tmp_f)
            if self._config_req.get('CharliecloudRequirement') is not None:
                self._stm.deploy_charliecloud(temp_file=tmp_f, ch_pre="srun")

        self.__deploy_bee_orchestrator(temp_file=tmp_f)

        self.blog.message("SBATCH CONTENTS", self._task_name, self.blog.msg)
        tmp_f.seek(0)
        self.blog.message(tmp_f.read().decode())

        tmp_f.seek(0)
        out = None
        if not test_only:
            out = self._run_sbatch(tmp_f.name)
        tmp_f.close()
        return out

    def specific_schedule(self):
        pass

    def specific_shutdown(self, job_id):
        # TODO: add identify other requirements?
        cmd = ['scancel', job_id]
        self._stm.run_popen_safe(cmd)

    def specific_move_file(self):
        pass

    def specific_execute(self):
        pass

    # private / supporting functions
    def _run_sbatch(self, file):
        cmd = ['sbatch', file]
        out = self._stm.run_popen_safe(command=cmd, err_exit=True)
        str_out = (str(out))[:-3]
        return str_out.rsplit(" ", 1)[1]

    def __resource_requirement(self, temp_file):
        """
        sbatch resource requirements, add to file
        :param temp_file: Target sbatch file (named temp file)
        """
        for key, value in self.\
                _config['requirements']['ResourceRequirement'].items():
            if key == 'custom':
                for c_key, c_value in value.items():
                    temp_file.write(bytes("#SBATCH {}={}\n".format(c_key,
                                                                   c_value),
                                    self._encode))
            else:
                gsl = self.__generate_sbatch_line(key, value)
                if gsl is not None:
                    temp_file.write(bytes(gsl + "\n", self._encode))
        # Set job-name equal if ID is available
        j_id = self._config.get('id', None)
        if j_id is not None:
            temp_file.write(bytes("#SBATCH --job-name={}".format(j_id),
                                  self._encode))

    @staticmethod
    def __generate_sbatch_line(key, value):
        """
        Generate single line for sbatch file
            e.g. #SBATCH --nodes=2
        :param key: sbatch key
                https://slurm.schedmd.com/sbatch.html
        :param value: associated with key
                Currently not verification!
        :return: sbatch line (string)
        """
        # supported sbtach scripting options
        result = {
            'numNodes': 'nodes',
            'jobTime': 'time',
            'partition': 'partition'
        }
        b = result.get(key, None)
        if b is None:
            return None
        else:
            a = "#SBATCH --"
            c = "=" + str(value)
            return a + b + c

    def __deploy_bee_orchestrator(self, temp_file):
        # TODO: re-write to account for log changes!
        """
        Scripting to launch bee_orchestrator, add to file
        :param temp_file: Target sbatch file (named temp file)
        """
        temp_file.write(bytes("\n# Launch BEE\n", self._encode))
        if self.in_mng is not None:
            in_flag = "--input {}".format(self._user_values)
        else:
            in_flag = ""
        bee_deploy = "bee-orchestrator --orc " + in_flag + self.blog.orc_flags() \
                     + " --task " + self._task_name
        temp_file.write(bytes("cd {} \n".format(self._file_loc), self._encode))
        temp_file.write(bytes(bee_deploy + "\n", self._encode))
