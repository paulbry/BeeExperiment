# system
import Pyro4
from os import path, getuid
from threading import Thread, Event
from pwd import getpwuid
from json import load
# project
from bee_internal.shared_tools import GeneralMethods


class BeeTask(Thread):
    def __init__(self, task_id, beefile, beelog, input_mng):
        Thread.__init__(self)

        # Task configuration
        self.platform = None
        self._sys_adapter = None
        self._manageSys = None
        self._beefile = beefile
        self._beefile_req = self._beefile.get('requirements')
        self._task_id = task_id
        self._task_label = self._beefile.get('label', 'BEE: {}'.
                                             format(self._task_id))

        # Logging conf. object -> BeeLogging(log, log_dest, quite)
        self.blog = beelog
        self._input_mng = input_mng
        self._g_share = GeneralMethods(self.blog)

        # System configuration
        self._user_name = getpwuid(getuid())[0]

        # Pyro4
        self._port = self.__pyro_port()
        ns = Pyro4.locateNS(port=self._port, hmac_key=getpwuid(getuid())[0])
        uri = ns.lookup("bee_launcher.daemon")
        self.remote = Pyro4.Proxy(uri)

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

    ###########################################################################
    # workerBees
    # A workerBees is a command made up of several components
    #   <systems> <command> <flags>
    # optionally <container> specifics can be supplemented between systems
    # and command.
    # e.g. srun -n 8 chrun -w --no-home /var/tmp/alpine -- sh hello.sh
    # TODO: clean up documentation
    ###########################################################################
    def _bee_tasks(self, bf_tasks, container_conf=None):
        for task in bf_tasks:
            cmd = []
            try:
                for wb in task:
                    system = self._workers_system(self._g_share.fetch_bf_val(task[wb],
                                                  'system', None, False, True))
                    if container_conf is not None and task[wb].get('container') is not None:
                        cmd += self._workers_containers(container_conf, task[wb])
                    cmd.append(wb)
                    cmd += self._workers_flags(self._g_share.fetch_bf_val(task[wb],
                                               'flags', {}, False, True))
                    self.blog.message("Executing: " + str(cmd), self._task_id,
                                      self.blog.msg)

                    out = self._sys_adapter.execute(cmd, system)
                    if out is not None and task[wb].get('output') is not None:
                        self._input_mng.update_vars(task[wb].get('output'), out)
            except KeyError as e:
                self.blog.message("Error while configuring workerBee specifed "
                                  "tasks.\n{}".format(repr(e)), self._task_id,
                                  self.blog.err)
                exit(1)

    def _workers_containers(self, cont_conf, task_conf):
        name = task_conf['container'].get('name', next(iter(cont_conf)))
        cmd = ['ch-run']
        for f in cont_conf[name].get('defaultFlags', {}):
            if isinstance(f, dict):
                for ok, ov in f.items():
                    cmd.append(self._input_mng.check_str(ok))
                    if ov is not None:
                        cmd.append(self._input_mng.check_str(ov))
            else:
                cmd.append(self._input_mng.check_str(f))

        for f in task_conf['container'].get('flags', {}):
            if isinstance(f, dict):
                for ok, ov in f.items():
                    cmd.append(self._input_mng.check_str(ok))
                    if ov is not None:
                        cmd.append(self._input_mng.check_str(ov))
            else:
                cmd.append(self._input_mng.check_str(f))

        loc = self._input_mng.check_str(cont_conf[name].get('tarDir', '/var/tmp'))
        cmd.append(loc + "/" + self._input_mng.check_str(name))
        cmd.append("--")
        return cmd

    def _workers_system(self, sys):
        cmd = []
        if sys is not None:
            tar = sys.get('manageSys', self._manageSys)
            if tar == 'localhost':
                return cmd
            else:
                cmd.append(tar)
            for f in self._g_share.fetch_bf_val(sys, 'flags', {},
                                                False, True):
                if isinstance(f, dict):
                    for ok, ov in f.items():
                        cmd.append(self._input_mng.check_str(ok))
                        if ov is not None:
                            cmd.append(self._input_mng.check_str(ov))
                else:
                    cmd.append(self._input_mng.check_str(f))
        return cmd

    def _workers_flags(self, flags):
        cmd = []
        for f in flags:
            if isinstance(f, dict):
                for ok, ov in f.items():
                    cmd.append(self._input_mng.check_str(ok))
                    if ov is not None:
                        cmd.append(self._input_mng.check_str(ov))
            else:
                cmd.append(self._input_mng.check_str(f))
        return cmd
