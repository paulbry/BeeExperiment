# system
import abc
# project
from bee_internal.tar_localhost import LocalhostAdaptee
from bee_internal.tar_ssh import SSHAdaptee
from bee_internal.tar_slurm import SlurmAdaptee


class Target(metaclass=abc.ABCMeta):
    """
    Define the domain-specific interface that Client uses
    """

    def __init__(self, system, config, file_loc, task_name, beelog, input_mng):
        self.__system = str(system).lower()

        # Logging conf. object -> BeeLogging(log, log_dest, quite)
        self.blog = beelog

        self._input_mng = input_mng

        # Beefile related
        self._config = config
        self._file_loc = file_loc
        self._task_name = task_name

        self._adaptee = None
        self.update_adaptee()

    def update_adaptee(self):
        if self.__system == "slurm":
            self._adaptee = SlurmAdaptee(self._config, self._file_loc,
                                         self._task_name, self.blog,
                                         self._input_mng)
        elif self.__system == "ssh":
            self._adaptee = SSHAdaptee(self._config, self._file_loc,
                                       self._task_name, self.blog,
                                       self._input_mng)
        elif self.__system == "localhost":
            self._adaptee = LocalhostAdaptee(self._config, self._file_loc,
                                             self._task_name, self.blog,
                                             self._input_mng)
        else:
            self.blog.message("Unable to support target system: {}".format(self.__system),
                              color=self.blog.err)
            exit(1)

    @abc.abstractmethod
    def execute(self, command, system=None):
        pass

    @abc.abstractmethod
    def shutdown(self):
        pass

    @abc.abstractmethod
    def move_file(self):
        pass


class Adapter(Target):
    """
    Adapt the interface of adaptee to the target request
    """

    def execute(self, command, system=None):
        return self._adaptee.specific_execute(command, system=None)

    def shutdown(self):
        self._adaptee.specific_shutdown()

    def move_file(self):
        self._adaptee.specific_move_file()
