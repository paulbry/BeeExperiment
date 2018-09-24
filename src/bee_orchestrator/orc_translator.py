# system
import abc
import Pyro4
from json import load
from os import getuid, path
from pwd import getpwuid
# project
from bee_internal.tar_localhost import LocalhostAdaptee
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

        # Pyro4
        self._port = self.__pyro_port()
        ns = Pyro4.locateNS(port=self._port, hmac_key=getpwuid(getuid())[0])
        uri = ns.lookup("bee_launcher.daemon")
        self.remote = Pyro4.Proxy(uri)

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
    def execute(self, command, system=None, capture_out=True):
        pass

    @abc.abstractmethod
    def shutdown(self):
        pass

    @abc.abstractmethod
    def move_file(self):
        pass

    @abc.abstractmethod
    def launch(self):
        pass

    @abc.abstractmethod
    def get_jobid(self):
        pass

    @abc.abstractmethod
    def get_remote_orc(self):
        pass

    @abc.abstractmethod
    def get_nodes(self):
        pass

    @staticmethod
    def __pyro_port():
        """
        Return port used by daemon (Pyro4)
        """
        conf_file = str(path.expanduser('~')) + "/.bee/port_conf.json"
        with open(conf_file, 'r') as fc:
            data = load(fc)
            port = data["pyro4-ns-port"]
        return port


class Adapter(Target):
    """
    Adapt the interface of adaptee to the target request
    """

    def execute(self, command, system=None, capture_out=True):
        return self._adaptee.specific_execute(command, system=system,
                                              capture_out=capture_out)

    def shutdown(self):
        self._adaptee.specific_shutdown()

    def move_file(self):
        self._adaptee.specific_move_file()

    def launch(self):
        self._adaptee.specific_launch()

    def get_jobid(self):
        return self._adaptee.specific_get_jobid()

    def get_remote_orc(self):
        return self._adaptee.specific_get_remote_orc()

    def get_nodes(self):
        return self._adaptee.specific_get_nodes()
