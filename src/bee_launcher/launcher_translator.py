# system
import abc
# project
from bee_internal.tar_slurm import SlurmAdaptee
from bee_internal.tar_ssh import SSHAdaptee
from bee_internal.tar_localhost import LocalhostAdaptee


class Target(metaclass=abc.ABCMeta):
    """
    Define the domain-specific interface that Client uses
    """
    def __init__(self, system, config, file_loc, task_name, beelog,
                 yml_in_file):
        self.__system = str(system).lower()

        # Logging conf. object -> BeeLogging(log, log_dest, quite)
        self.blog = beelog

        # Beefile related
        self._config = config
        self._file_loc = file_loc
        self._task_name = task_name

        # Input file
        self._yml_in_file = yml_in_file

        self._adaptee = None
        self.update_adaptee()

    def update_adaptee(self):
        if self.__system == "slurm":
            self._adaptee = SlurmAdaptee(self._config, self._file_loc,
                                         self._task_name, self.blog,
                                         self._yml_in_file)

        elif self.__system == "localhost":
            self._adaptee = LocalhostAdaptee(self._config, self._file_loc,
                                             self._task_name, self.blog,
                                             self._yml_in_file)
        else:
            self.blog.message("Unable to support target system: " + self.__system
                              + " attempting ssh.", color=self.blog.warn)
            self._adaptee = SSHAdaptee(self._config, self._file_loc,
                                       self._task_name, self.blog,
                                       self._yml_in_file)

    @abc.abstractmethod
    def allocate(self, test_only=False):
        #######################################################################
        # Should return tuple stdout
        # out: Unique job idea (signify successful allocation) or None (failed)
        # Print error message(s) and fail allocation if applicable
        #######################################################################
        pass

    @abc.abstractmethod
    def schedule(self):
        pass

    @abc.abstractmethod
    def shutdown(self, job_id):
        pass

    @abc.abstractmethod
    def move_file(self):
        pass


class Adapter(Target):
    """
    Adapt the interface of adaptee to the target request
    """
    def allocate(self, test_only=False):
        return self._adaptee.specific_allocate(test_only=test_only)

    def schedule(self):
        self._adaptee.specific_schedule()

    def shutdown(self, job_id):
        self._adaptee.specific_shutdown(job_id)

    def move_file(self):
        self._adaptee.specific_move_file()
