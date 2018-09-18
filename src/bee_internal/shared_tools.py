# system
from subprocess import Popen, PIPE, CalledProcessError, STDOUT
from bee_monitor.db_orc import OrchestratorDB


class GlobalMethods(object):
    def __init__(self, beefile, task_name, beelog,
                 bldaemon=None, job_id=None):

        # constants
        self._encode = 'UTF-8'

        # task / configuration
        self._beefile = beefile
        self._beefile_req = self._beefile.get('requirements')
        self._task_name = task_name
        self._job_id = job_id

        # objects
        self.blog = beelog  # BeeLogging
        self.orc_db = OrchestratorDB(self.blog)

        # daemon for ORC control
        self.remote = bldaemon

    def fetch_bf_val(self, dictionary, key, default=None,
                     quit_err=False, silent=False, status=99):
        try:
            return dictionary[key]
        except KeyError:
            if not quit_err:
                msg = "User defined value for [{}] was not found, default" \
                      " value: {} used.".format(key, default)
                if not silent:
                    self.blog.message(msg=msg, color=self.blog.warn)
                self.__fetch_orc_control(status, "fetch_bf_val()", msg, None, 0)
                return default
            else:
                msg = "Key: {} was not found!".format(key)
                self.blog.message(msg=msg, color=self.blog.err)
                self.__fetch_orc_control(status, "fetch_bf_val()", None, msg, 1)

    def __fetch_orc_control(self, status, cmd, out, err, code):
        self.orc_db.new_orc(task_id=self._task_name,
                            status=status, job_id=self._job_id,
                            command=cmd, std_output=out,
                            std_err=err, exit_status=code)
        if code > 0:
            if self.remote is not None:
                self.remote.shutdown_daemon()
            exit(code)

    def run_popen_safe(self, command, err_exit=True):
        """
        Run command via Popen
        :param command:
        :param err_exit: Exit (w/status 1) on exception
        :return: stdout on success, None on failure
        """
        r_cmd = (''.join(str(x) + " " for x in command))
        self.blog.message("Executing: {}".format(r_cmd))
        try:
            p = Popen(command, stdout=PIPE, stderr=STDOUT)
            out, err = p.communicate()
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

    ###########################################################################
    # Orchestration / Runtime related methods
    ###########################################################################
    def run_popen_orc(self, command, cap_out):
        """
        Run command (origniating with orchestration) via Popen
        :param command:
        :param cap_out:
        :return: output, exitStatus
        """
        r_cmd = (''.join(str(x) + " " for x in command))
        self.blog.message("Executing: {}".format(r_cmd))
        try:
            p = Popen(command, stdout=PIPE)
            if cap_out:
                out = p.communicate()[0]
                return (out.decode('utf8')).rstrip(), p.returncode
            else:
                return "No output captured", p.wait()
        except CalledProcessError as err:
            return err, 1
        except OSError as err:
            return err, 1

    def out_control(self, cmd, out, status):
        """

        :param cmd:
        :param out:
        :param status:
        :return:
        """
        self.orc_db.new_orc(task_id=self._task_name,
                            status=status, job_id=self._job_id,
                            command=cmd, std_output=out,
                            std_err=None, exit_status=0,
                            event="Subprocess")

    def err_control(self, code, cmd, out, err, status, err_exit=True):
        self.blog.message(msg="Error during: {}\n{}".format(cmd, err), color=self.blog.err)
        self.orc_db.new_orc(task_id=self._task_name,
                            status=status, job_id=self._job_id,
                            command=cmd, std_output=out,
                            std_err=err, exit_status=code,
                            event="Subprocess")
        if code > 0 and err_exit:
            self.remote.shutdown_daemon()
            exit(code)

    def general_control(self, status, cmd=None, out=None, err=None,
                        code=None, event=None):
        self.orc_db.new_orc(task_id=self._task_name,
                            status=status, job_id=self._job_id,
                            command=cmd, std_output=out,
                            std_err=err, exit_status=code,
                            event=event)


class TranslatorMethods(GlobalMethods):
    def __init__(self, beefile, task_name, beelog, bldaemon=None,
                 job_id=None):
        GlobalMethods.__init__(self, beefile, task_name, beelog, bldaemon,
                               job_id)

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
                _beefile['requirements']['SoftwareModules'].items():
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
        env_dict = self._beefile_req.get('EnvVarRequirements', {})
        for f in env_dict.get('envDev', {}):
            for ok, ov in f.items():
                export = "export {}={}:${}".format(input_mng.check_str(ok),
                                                   input_mng.check_str(ov),
                                                   input_mng.check_str(ok))
                temp_file.write(bytes(export + "\n", 'UTF-8'))
        for f in env_dict.get('sourceDef', {}):
            if isinstance(f, dict):
                for ok, ov in f.items():
                    source = "source {}".format(input_mng.check_str(ok))
                    if ov is not None:
                        source += " " + format(input_mng.check_str(ov))
                    temp_file.write(bytes(source + "\n", 'UTF-8'))

    def deploy_charliecloud(self, temp_file, ch_pre=None):
        """
        Identify and un-tar Charliecloud container, add to file
        :param temp_file: Target sbatch file (named temp file)
        :param ch_pre: Prefix (string) used before ch-tar2dir
                    e.g srun
        """
        temp_file.write(bytes("\n# Deploy Charliecloud Containers\n", self._encode))
        for cc in self._beefile_req.get('CharliecloudRequirement', {}):
            cc_task = self._beefile_req['CharliecloudRequirement'][cc]
            if ch_pre is not None:
                cc_deploy = str(ch_pre) + " ch-tar2dir "
            else:
                cc_deploy = "ch-tar2dir "
            cc_deploy += str(cc_task['source']) + " " \
                         + str(cc_task.get('tarDir', '/var/tmp')) + "\n"
            temp_file.write(bytes(cc_deploy, self._encode))
