# 3rd party
from termcolor import cprint


class BeeLogging(object):
    def __init__(self, log, log_dest, quite):
        self._log = log  # boolean
        self._log_dest = log_dest  # string
        self._quite = quite  # boolean

        # Termcolor messages
        self.__error_color = 'red'
        self.__message_color = 'cyan'
        self.__warning_color = 'yellow'
        self.__database_color = 'green'

    def orc_flags(self):
        """
        :return: flags for use in orchestrator (string)
                targeting inclusion in allocation script
                example; "--logflag --logfile=/test.log"
        """
        f = ""
        if self._log:
            f += "--logflag "
        if self._log_dest != "/var/tmp/bee.log":
            f += "--logfile={} ".format(self._log_dest)
        if self._quite:
            f += " --quite "
        return f

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
        """
        Print message with supplied details, utlizes CLI supplied
        flags (log_dest & log_flag)
        :param msg: Message to be printed/streamed to console
        :param task_name: Name of task append and used to log
                (optional)
        :param color: termcolor (optional)
        """
        msg_q = self._quite
        if color is not None and color == self.__error_color:
            msg_q = False

        if not msg_q:
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
