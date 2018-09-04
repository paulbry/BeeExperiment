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

    def specific_execute(self, command, system=None):
        self.__run_popen(command)

    def specific_shutdown(self):
        pass

    def specific_move_file(self):
        pass

    # Task management support functions (public)
    def __run_popen(self, cmd):
        # TODO: document
        cprint("Executing: " + str(cmd), )
        try:
            p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
            out, err = p.communicate()
            print("stdout: ", repr(out))
            print("stderr: ", repr(err))
        except CalledProcessError as e:
            cprint("Error during - " + str(cmd) + "\n" + str(e),
                   self._error_color)
            exit(1)
        except OSError as e:
            cprint("Error during - " + str(cmd) + "\n" + str(e),
                   self._error_color)
            exit(1)
