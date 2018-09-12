# system
import Pyro4
from os import path, getuid
from threading import Thread, Event
from pwd import getpwuid
from json import load


class BeeTask(Thread):
    def __init__(self, task_id, beefile, beelog, input_mng):
        Thread.__init__(self)

        # Logging conf. object -> BeeLogging(log, log_dest, quite)
        self.blog = beelog

        self._input_mng = input_mng

        # Task configuration
        self.platform = None
        self._sys_adapter = None
        self._beefile = beefile
        self._beefile_req = self._beefile.get('requirements')
        self._task_id = task_id
        self._task_label = self._beefile.get('label', 'BEE: {}'.
                                             format(self._task_id))

        # System configuration
        self._user_name = getpwuid(getuid())[0]

        # Pyro4
        self._port = self.__pyro_port()
        ns = Pyro4.locateNS(port=self._port, hmac_key=self._user_name)
        uri = ns.lookup("bee_launcher.daemon")
        self._bldaemon = Pyro4.Proxy(uri)

        # Events for workflow
        self.__begin_event = None
        self.__end_event = None
        self.__event_list = []

    # Event/Trigger management
    @property
    def begin_event(self):
        return self.__begin_event

    @begin_event.setter
    def begin_event(self, flag):
        # TODO: document
        if flag == 0:
            self.__begin_event = Event()
        elif flag == 1:
            self.__begin_event.set()
        else:
            self.__begin_event.clear()

    @property
    def end_event(self):
        return self.__end_event

    @end_event.setter
    def end_event(self, flag):
        # TODO: document
        if flag == 0:
            self.__end_event = Event()
        elif flag == 1:
            self.__end_event.set()
        else:
            self.__end_event.clear()

    @property
    def event_list(self):
        return self.__event_list

    @event_list.setter
    def event_list(self, new_event):
        """
        Append event to event_list
        :param new_event:
        """
        self.__event_list.append(new_event)

    # Standard BEE methods
    def run(self):
        pass

    def launch(self):
        pass

    def execute_workers(self):
        pass

    def execute_base(self):
        """
        Goal: Execute program/script specified in baseCommand, ensure
        that all inputs/user-defined variables are properly accounted for
        """
        pass

    def terminate(self, clean=False):
        pass

    # Task management support functions (private)
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
