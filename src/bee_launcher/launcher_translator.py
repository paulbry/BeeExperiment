# system
import abc
# project
from bee_internal.tar_slurm import SlurmAdaptee
from bee_internal.tar_localhost import LocalhostAdaptee


class Target(metaclass=abc.ABCMeta):
    """
    Define the domain-specific interface that Client uses
    """
    def __init__(self, system, config, file_loc, task_name, beelog,
                 input_mng):
        # task / configuration
        self.__system = str(system).lower()
        self._config = config
        self._file_loc = file_loc
        self._task_name = task_name
        self.remote = None

        # objects
        self.blog = beelog  # BEE_LOGGING
        self._input_mng = input_mng
        self._adaptee = None
        self.update_adaptee()

    def update_adaptee(self):
        if self.__system == "slurm":
            self._adaptee = SlurmAdaptee(self._config, self._file_loc,
                                         self._task_name, self.blog,
                                         self._input_mng, self.remote)

        elif self.__system == "localhost":
            self._adaptee = LocalhostAdaptee(self._config, self._file_loc,
                                             self._task_name, self.blog,
                                             self._input_mng, self.remote)
        else:
            self.blog.message("Unable to support target system: {}".format(self.__system),
                              color=self.blog.err)
            exit(1)

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
