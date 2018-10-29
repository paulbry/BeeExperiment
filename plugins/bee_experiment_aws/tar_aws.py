# system
from os import environ
from tempfile import NamedTemporaryFile
# project
from bee_internal.shared_tools import TranslatorMethods


class AWSAdaptee:
    def __init__(self, config, file_loc, task_name, beelog, input_mng,
                 remote=None):
        # constants
        self._encode = 'UTF-8'

        # task /configuration
        self._beefile = config
        if self._beefile is not None:
            self._beefile_req = self._beefile.get('requirements')
        else:
            self._beefile_req = {}
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
            out = self._run_sbatch(tmp_f.name, dependency)
        tmp_f.close()
        return out

    def specific_shutdown(self, job_id):
        cmd = ['scancel', job_id]
        return self.stm.run_popen_code(cmd)

    def specific_move_file(self):
        pass

    def specific_launch(self):
        pass

    def specific_execute(self, command, system=None, capture_out=True):
        if system is not None:
            pass
        else:  # run via ??? (take responsibility)
            pass

    @staticmethod
    def specific_get_jobid():
        pass

    def specific_get_remote_orc(self):
        return self.remote

    def specific_get_nodes(self):
        pass

    ###########################################################################
    # Protected/Private supporting functions
    ###########################################################################
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
