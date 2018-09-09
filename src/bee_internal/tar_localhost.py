# system
from tempfile import NamedTemporaryFile
from datetime import datetime
from time import time
# project
from bee_internal.shared_tools import TranslatorMethods
from bee_internal.in_out_manage import InputManagement


class LocalhostAdaptee:
    def __init__(self, config, file_loc, task_name, beelog, yml_in_file):
        self._config = config
        if self._config is not None:
            self._config_req = self._config.get('requirements')
        self._file_loc = file_loc
        self._task_name = task_name
        self._encode = 'UTF-8'

        # Logging conf. object -> BeeLogging(log, log_dest, quite)
        self.blog = beelog

        self._user_values = yml_in_file
        self._beefile_input = self._config.get('inputs')
        if self._user_values is not None and self._beefile_input is not None:
            self.in_mng = InputManagement(self._beefile_input, self._user_values,
                                          self.blog)

        # Shared tools
        self._stm = TranslatorMethods(config=self._config,
                                      file_loc=self._file_loc,
                                      task_name=self._task_name,
                                      beelog=self.blog)

    def specific_allocate(self, test_only=False):
        # TODO: document
        tmp_f = NamedTemporaryFile()
        tmp_f.write(bytes("#!/bin/bash\n\n", 'UTF-8'))
        #######################################################################
        # Prepare script
        # TODO: further document
        #######################################################################
        if self._config_req is not None:
            if self._config_req.get('ResourceRequirement') is not None:
                self.__resource_requirement(temp_file=tmp_f)
            if self._config_req.get('SoftwareModules') is not None:
                self._stm.software_modules(temp_file=tmp_f)
            if self._config_req.get('EnvVarRequirements') is not None:
                self._stm.env_variables(temp_file=tmp_f)
            if self._config_req.get('CharliecloudRequirement') is not None:
                self._stm.deploy_charliecloud(temp_file=tmp_f)

        job_id = datetime.fromtimestamp(time()).strftime('%m%d-%H%M%S')
        self.__deploy_bee_orchestrator(temp_file=tmp_f)

        self.blog.message("LOCALHOST SCRIPT CONTENTS", self._task_name,
                          self.blog.msg)
        tmp_f.seek(0)
        self.blog.message(tmp_f.read().decode())

        tmp_f.seek(0)
        out = None
        if not test_only:
            out = "lh-{}".format(job_id)
            with open(out, 'a') as s_file:
                s_file.write(tmp_f.read().decode())
            self._run_screen(out, out)
        tmp_f.close()
        return out

    def specific_schedule(self):
        pass

    def specific_shutdown(self, job_id):
        # TODO: identify other requirements
        cmd = ['screen', '-X', '-S', job_id, 'quit']
        self._stm.run_popen_safe(cmd)

    def specific_move_file(self):
        pass

    def specific_execute(self, command, system=None):
        # TODO: add DB related steps?
        if system is not None:
            self._stm.run_popen_safe(command)
        else:  # run via localhost (take responsibility)
            self._stm.run_popen_safe(command)

    def _run_screen(self, file, job_id):
        # TODO: clean up Popen and document
        cmd = ['screen', '-S', job_id, '-d', '-m', 'bash', file]
        self._stm.run_popen_safe(cmd)

    def __resource_requirement(self, temp_file):
        # TODO: identify resources that should/could be affected
        pass

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
