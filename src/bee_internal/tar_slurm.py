# system
from tempfile import NamedTemporaryFile
from os import environ
# project
from bee_internal.shared_tools import TranslatorMethods


class SlurmAdaptee:
    def __init__(self, config, file_loc, task_name, beelog, input_mng,
                 remote=None):
        # constants
        self._encode = 'UTF-8'

        # task /configuration
        self._beefile = config
        self._beefile_req = self._beefile.get('requirements')
        self._file_loc = file_loc
        self._task_name = task_name

        # daemon for ORC control
        self.remote = remote

        # objects
        self.blog = beelog
        self._input_mng = input_mng
        self.stm = TranslatorMethods(beefile=self._beefile,
                                     task_name=self._task_name, beelog=self.blog,
                                     bldaemon=self.remote, job_id=None)

    ###########################################################################
    # Adapter functions
    # orc_translator.py & launch_translator.py
    ###########################################################################
    def specific_allocate(self, test_only=False, dependency=None):
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
        if self._beefile_req is not None:
            if self._beefile_req.get('ResourceRequirement') is not None:
                self.__resource_requirement(temp_file=tmp_f)
            else:
                self.blog.message("ResourceRequirement key is required for "
                                  "allocation", self._task_name, self.blog.err)
            if self._beefile_req.get('SoftwareModules') is not None:
                self.stm.software_modules(temp_file=tmp_f)
            if self._beefile_req.get('EnvVarRequirements') is not None:
                self.stm.env_variables(temp_file=tmp_f, input_mng=self._input_mng)
            if self._beefile_req.get('CharliecloudRequirement') is not None:
                self.stm.deploy_charliecloud(temp_file=tmp_f, ch_pre="srun")

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

    def specific_shutdown(self, job_id):
        cmd = ['scancel', job_id]
        self.stm.run_popen_safe(cmd)

    def specific_move_file(self):
        pass

    def specific_launch(self):
        pass

    def specific_execute(self, command, system=None, capture_out=True):
        if system is not None:
            return self.stm.run_popen_orc(system + command, capture_out)
        else:  # run via SRUN (take responsibility)
            cmd = ['srun'] + command
            return self.stm.run_popen_orc(cmd, capture_out)

    @staticmethod
    def specific_get_jobid():
        return environ.get('SLURM_JOB_ID')

    def specific_get_remote_orc(self):
        return self.remote

    def specific_get_nodes(self):
        nl_env_val = environ.get("SLURM_JOB_NODELIST")
        sys_name = nl_env_val[:nl_env_val.find("[")]
        node_list = []
        nums = ["0", "1", "2", "3", "4",
                "5", "6", "7", "8", "9"]

        if nl_env_val is not None:
            os_n_list = nl_env_val[nl_env_val.find("[") + 1:
                                   nl_env_val.find("]")]
            tmp = ''
            i = 0
            while i < len(os_n_list):
                if os_n_list[i] in nums:
                    tmp += os_n_list[i]
                    i += 1
                elif os_n_list[i] == ',':
                    node_list.append(sys_name + tmp)
                    tmp = ''
                    i += 1
                elif os_n_list[i] == '-':
                    next_p = os_n_list.find(',', i)
                    if next_p < 0:
                        next_p = len(os_n_list)

                    tmp_end_val = os_n_list[i + 1:next_p]
                    val_len = len(tmp_end_val)
                    while tmp != tmp_end_val:
                        node_list.append(sys_name + tmp)
                        tmp = str(int(tmp) + 1)
                        while len(tmp) < val_len:
                            tmp = "0" + tmp
                    tmp = ''
                    i += 1

            if tmp != '':
                node_list.append(sys_name + tmp)

        return node_list

    ###########################################################################
    # Protected/Private supporting functions
    ###########################################################################
    def _run_sbatch(self, file):
        cmd = ['sbatch', file]
        out = self.stm.run_popen_safe(command=cmd, err_exit=True)
        str_out = (str(out))[:-3]
        return str_out.rsplit(" ", 1)[1]

    def __resource_requirement(self, temp_file):
        """
        sbatch resource requirements, add to file
        :param temp_file: Target sbatch file (named temp file)
        """
        for key, value in self.\
                _beefile['requirements']['ResourceRequirement'].items():
            if key == 'custom':
                for f in value:
                    if type(f) is dict:
                        ok, ov = f.items()
                        temp_file.write(bytes("#SBATCH {}={}\n".
                                              format(self._input_mng.check_str(ok),
                                                     self._input_mng.check_str(ov)),
                                        self._encode))
            else:
                gsl = self.__generate_sbatch_line(key, value)
                if gsl is not None:
                    temp_file.write(bytes(gsl + "\n", self._encode))
        # Set job-name equal if ID is available
        j_id = self._beefile.get('id', None)
        if j_id is not None:
            temp_file.write(bytes("#SBATCH --job-name={}".format(j_id),
                                  self._encode))
        temp_file.write(bytes("\n", self._encode))

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
        """
        Scripting to launch bee_orchestrator, add to file
        :param temp_file: Target sbatch file (named temp file)
        """
        temp_file.write(bytes("\n# Launch BEE\n", self._encode))
        in_flag = ""
        if self._input_mng.yml_file_name is not None:
            in_flag = "--input {}".format(self._input_mng.yml_file_name)
        bee_deploy = "bee-orchestrator --orc " + in_flag + self.blog.orc_flags() \
                     + " -t " + self._task_name
        temp_file.write(bytes("cd {} \n".format(self._file_loc), self._encode))
        temp_file.write(bytes(bee_deploy + "\n", self._encode))
