# system
from termcolor import cprint


class BeeLogging(object):
    def __init__(self, log, log_dest, quite):
        self._log = log
        self._log_dest = log_dest
        self._quite = quite

        # Termcolor messages
        self.__error_color = 'red'
        self.__message_color = 'cyan'
        self.__warning_color = 'yellow'
        self.__database_color = 'green'

    @property
    def err(self):
        return self.__error_color

    @property
    def msg(self):
        return self.__message_color

    @property
    def warn(self):
        return self.__warning_color

    @property
    def dbase(self):
        return self.__database_color

    def message(self, msg, task_name=None, color=None):
        # TODO: document
        if not self._quite:
            if color is not None:
                if task_name is not None:
                    cprint("[{}] {}".format(task_name, msg), color)
                else:
                    cprint(str(msg), color)
            else:
                if task_name is not None:
                    print("[{}] {}".format(task_name, msg))
                else:
                    print(str(msg))
