# system
from tempfile import NamedTemporaryFile
from datetime import datetime
from time import time
from os import environ
# project
from bee_internal.shared_tools import TranslatorMethods


class LocalhostAdaptee:
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
    def specific_allocate(self, test_only=False):
        tmp_f = NamedTemporaryFile()
        tmp_f.write(bytes("#!/bin/bash\n\n", 'UTF-8'))
        #######################################################################
        # Prepare script
        # TODO: further document
        #######################################################################
        if self._beefile_req is not None:
            if self._beefile_req.get('ResourceRequirement') is not None:
                self.__resource_requirement(temp_file=tmp_f)
            if self._beefile_req.get('SoftwareModules') is not None:
                self.stm.software_modules(temp_file=tmp_f)
            if self._beefile_req.get('EnvVarRequirements') is not None:
                self.stm.env_variables(temp_file=tmp_f, input_mng=self._input_mng)
            if self._beefile_req.get('CharliecloudRequirement') is not None:
                self.stm.deploy_charliecloud(temp_file=tmp_f)

        job_id = datetime.fromtimestamp(time()).strftime('%m%d-%H%M%S')
        self.__deploy_bee_orchestrator(temp_file=tmp_f)

        tmp_f.write(bytes("\nrm -- \"$0\"\n", self._encode))

        self.blog.message("LOCALHOST SCRIPT CONTENTS", self._task_name,
                          self.blog.msg)
        tmp_f.seek(0)
        self.blog.message(tmp_f.read().decode())

        tmp_f.seek(0)
        out = None
        if not test_only:
            out = "lh-{}.beescript".format(job_id)
            with open(out, 'a') as s_file:
                s_file.write(tmp_f.read().decode())
            self._run_screen(out, out)
        tmp_f.close()
        return out

    def specific_schedule(self):
        # TODO: utilize cron ?
        pass

    def specific_shutdown(self, job_id):
        cmd = ['screen', '-X', '-S', job_id, 'quit']
        self.stm.run_popen_safe(cmd)

    def specific_move_file(self):
        # TODO: identify requirements
        pass

    def specific_execute(self, command, system):
        if system:
            return self.stm.run_popen_orc(system + command)
        else:  # run via localhost (take responsibility)
            return self.stm.run_popen_orc(command)

    @staticmethod
    def specific_get_jobid():
        return environ.get('STY')

    def specific_get_remote_orc(self):
        return self.remote

    @staticmethod
    def specific_get_nodes():
        return []

    ###########################################################################
    # Protected/Private supporting functions
    ###########################################################################
    def _run_screen(self, file, job_id):
        cmd = ['screen', '-S', job_id, '-d', '-m', 'bash', file]
        self.stm.run_popen_safe(cmd)

    def __resource_requirement(self, temp_file):
        # TODO: identify resources that should/could be affected
        pass

    def __deploy_bee_orchestrator(self, temp_file):
        """
        Scripting to launch bee_orchestrator, add to file
        :param temp_file: Target sbatch file (named temp file)
        """
        temp_file.write(bytes("\n# Launch BEE\n", self._encode))
        in_flag = ""
        if self._input_mng.yml_file_name is not None:
            in_flag = "--input {} ".format(self._input_mng.yml_file_name)
        bee_deploy = "bee-orchestrator --orc " + in_flag + self.blog.orc_flags() \
                     + "--task " + self._task_name
        temp_file.write(bytes("cd {} \n".format(self._file_loc), self._encode))
        temp_file.write(bytes(bee_deploy + "\n", self._encode))