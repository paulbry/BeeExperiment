from subprocess import Popen, PIPE, CalledProcessError, \
    STDOUT
from termcolor import cprint


class LocalhostAdaptee:
    def __init__(self, config, file_loc, task_name):
        self._config = config
        self._config_req = self._config['requirements']
        self._file_loc = file_loc
        self._task_name = task_name
        self._encode = 'UTF-8'

        # Termcolor (temp)
        self._message_color = "cyan"
        self._error_color = "red"
        self._warning_color = "yellow"

    def specific_allocate(self):
        pass

    def specific_schedule(self):
        pass

    def specific_shutdown(self):
        pass

    def specific_move_file(self):
        pass

    def specific_execute(self, command, system=None):
        # TODO: add DB related steps?
        if system is not None:
            self._run_popen_safe(command)
        else:  # run via localhost (take responsibility)
            self._run_popen_safe(command)

    # Task management support functions (public)
    # TODO: Move to shared location (bee-internal)?
    def _run_popen_safe(self, command, err_exit=True):
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
        self._handle_message("Executing: " + str(command))
        try:
            p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
            out, err = p.communicate()
            print("stdout: ", repr(out))
            print("stderr: ", repr(err))
            return out
        except CalledProcessError as e:
            self._handle_message(msg="Error during - " + str(command) + "\n" +
                                 str(e), color=self._error_color)
            if err_exit:
                exit(1)
            return None
        except OSError as e:
            self._handle_message(msg="Error during - " + str(command) + "\n" +
                                 str(e), color=self._error_color)
            if err_exit:
                exit(1)
            return None

    # Task management support functions (private)
    def _handle_message(self, msg, color=None):
        """
        :param msg: To be printed to console
        :param color: If message is be colored via termcolor
                        Default = none (normal print)
        """

        if color is None:
            print("[{}] {}".format(self._task_name, msg))
        else:
            cprint("[{}] {}".format(self._task_name, msg), color)