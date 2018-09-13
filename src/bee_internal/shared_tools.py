# system
from subprocess import Popen, PIPE, CalledProcessError, STDOUT


class GlobalMethods(object):
    def __init__(self, config, file_loc, task_name, beelog):
        self._config = config
        if self._config is not None:
            self._config_req = self._config.get('requirements')
        self._file_loc = file_loc
        self._task_name = task_name
        self._encode = 'UTF-8'

        # Logging conf. object -> BeeLogging(log, log_dest, quite)
        self.blog = beelog

    def fetch_bf_val(self, dictionary, key, default=None,
                     quit_err=False, silent=False):
        # TODO: document
        try:
            return dictionary[key]
        except KeyError:
            if not quit_err:
                if not silent:
                    self.blog.message("User defined value for [" +
                                      str(key) + "] was not found, default value: "
                                      + str(default) + " used.",
                                      color=self.blog.warn)
                return default
            else:
                self.blog.message("Key: " + str(key) + " was not found",
                                  color=self.blog.err)
            exit(1)

    def run_popen_safe(self, command, err_exit=True):
        """
        Run defined command via Popen, try/except statements
        built in and message output when appropriate
        :param command: Command to be run
        :param err_exit: Exit upon error, default True
        :return: stdout from p.communicate() based upon results
                    of command run via subprocess
                None, error message returned if except reached
                    and err_exit=False
        """
        self.blog.message("Executing: " + str(command))
        # TODO: improve for larger program requirements? Stream output?
        try:
            p = Popen(command, stdout=PIPE, stderr=STDOUT)
            out, err = p.communicate()
            self.blog.message("\tstdout: {}".format(repr(out)))
            self.blog.message("\tstderr: {}".format(repr(err)))
            return out.decode('utf8')
        except CalledProcessError as e:
            self.blog.message(msg="Error during - " + str(command) + "\n" +
                                  str(e), color=self.blog.err)
            if err_exit:
                exit(1)
            return None
        except OSError as e:
            self.blog.message(msg="Error during - " + str(command) + "\n" +
                                  str(e), color=self.blog.err)
            if err_exit:
                exit(1)
            return None


class TranslatorMethods(GlobalMethods):
    def __init__(self, config, file_loc, task_name, beelog):
        GlobalMethods.__init__(self, config, file_loc, task_name, beelog)

    ###########################################################################
    # General script generation modules utilized during allocation
    # These can be shared by a number of possible translation targets
    ###########################################################################
    def software_modules(self, temp_file):
        """
        Module load <target(s)>, add to file
        :param temp_file: Target sbatch file (named temp file)
        """
        temp_file.write(bytes("\n# Load Modules\n", self._encode))
        for key, value in self. \
                _config['requirements']['SoftwareModules'].items():
            module = "module load {}".format(key)
            if value is not None:
                module += "/" + str(value.get('version', ''))
            temp_file.write(bytes(module + "\n", 'UTF-8'))

    def env_variables(self, temp_file, input_mng):
        """
        Added source <key> <value> and export <key> <value>:$<key>
        in order to establish the environment
        :param temp_file: Target sbatch file (named temp file)
        :param input_mng: InputMangement object
        """
        temp_file.write(bytes("\n# Environmental Requirements\n", self._encode))
        env_dict = self._config_req['EnvVarRequirements']
        for f in self.fetch_bf_val(env_dict, 'envDev', {}, False, True):
            for ok, ov in f.items():
                export = "export {}={}:${}".format(input_mng.check_str(ok),
                                                   input_mng.check_str(ov),
                                                   input_mng.check_str(ok))
                temp_file.write(bytes(export + "\n", 'UTF-8'))
        for f in self.fetch_bf_val(env_dict, 'sourceDef', {}, False, True):
            if isinstance(f, dict):
                for ok, ov in f.items():
                    source = "source {}".format(input_mng.check_str(ok))
                    if ov is not None:
                        source = "source {}".format(input_mng.check_str(f))
                    temp_file.write(bytes(source + "\n", 'UTF-8'))

    def deploy_charliecloud(self, temp_file, ch_pre=None):
        """
        Identify and un-tar Charliecloud container, add to file
        :param temp_file: Target sbatch file (named temp file)
        :param ch_pre: Prefix (string) used before ch-tar2dir
                    e.g srun
        """
        temp_file.write(bytes("\n# Deploy Charliecloud Container\n", self._encode))
        # TODO: better error handling?
        # TODO: options for build/pull?
        for cc in self._config_req['CharliecloudRequirement']:
            cc_task = self._config_req['CharliecloudRequirement'][cc]
            if ch_pre is not None:
                cc_deploy = str(ch_pre) + " ch-tar2dir "
            else:
                cc_deploy = "ch-tar2dir "
            cc_deploy += str(cc_task['source']) + " " \
                         + str(cc_task.get('tarDir', '/var/tmp')) + "\n"
            temp_file.write(bytes(cc_deploy, self._encode))


class GeneralMethods(GlobalMethods):
    def __init__(self, beelog):
        GlobalMethods.__init__(self, None, None, None, beelog)
