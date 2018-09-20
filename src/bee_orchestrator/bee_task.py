# system
import Pyro4
import argparse
from os import path, getuid
from threading import Thread, Event
from pwd import getpwuid
from json import load
# project
from bee_launcher.bee_launch import BeeArguments


class BeeTask(Thread):
    def __init__(self, task_id, beefile, beelog, input_mng):
        Thread.__init__(self)

        self._current_status = 00

        # Task configuration
        self.platform = None
        self._sys_adapter = None
        self._manageSys = None
        self._beefile = beefile
        self._beefile_req = self._beefile.get('requirements')
        self._task_id = task_id
        self._task_label = self._beefile.get('label', 'BEE: {}'.
                                             format(self._task_id))
        self._job_id = None
        self.global_m = None

        # Logging conf. object -> BeeLogging(log, log_dest, quite)
        self.blog = beelog
        self._input_mng = input_mng

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

    # Task management support functions (private/protected)
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

    def _status_change(self, new):
        """
        Change status to new (argument) status and log in orc.db
        Can only be called  GlobalMethods object created!
        """
        self.current_status = new
        self.global_m.general_control(status=self.current_status,
                                      event="Status change")

    ###########################################################################
    # workerBees
    # A workerBees is a command made up of several components
    #   <systems> <command> <flags>
    # optionally <container> specifics can be supplemented between systems
    # and command.
    # e.g. srun -n 8 chrun -w --no-home /var/tmp/alpine -- sh hello.sh
    # TODO: clean up documentation
    #
    # [stdOut, exitStatus, command, outputTarget]
    ###########################################################################
    def _sub_bees(self, sub_task):
        """

        :param sub_task:
        :return:
        """
        result = [None, 0, str(sub_task), None]
        try:
            for wb in sub_task:
                args = argparse.Namespace(launch_task=[wb],
                                          log_dest=[sub_task[wb].get('log_dest',
                                                                     '/var/tmp/bee.log'),
                                                    sub_task[wb].get('inputFile')
                                                    ],
                                          logflag=sub_task[wb].get('logFlag', False),
                                          quite=sub_task[wb].get('quite', False),
                                          testonly=False)
                ba = BeeArguments(self.blog)

                ty = str(sub_task[wb].get('type')).lower()
                if ty == 'in-situ':
                    result[0] = ba.opt_launch(args)
                elif ty == 'offline':
                    # TODO: implement check in adapter
                    self.blog.message("offline SubBee not supported yet!",
                                      color=self.blog.err)
                return result
        except KeyError as e:
            msg = "Error while configuring workerBee specified " \
                  "subBee.\n{}".format(repr(e))
            self.blog.message(msg, self._task_id, self.blog.err)
            return [msg, 1, None, None]

    def _bee_tasks(self, bf_task, container_conf=None):
        """

        :param bf_task:
        :param container_conf:
        :return:
        """
        try:
            for wb in bf_task:
                cmd = []
                system = self._workers_system(bf_task[wb].get('system', None))

                if bf_task[wb].get('output') is not None:
                    capture_out = True
                else:
                    capture_out = False

                if container_conf is not None and bf_task[wb].get('container') is not None:
                    cmd += self._workers_containers(container_conf, bf_task[wb])
                cmd.append(wb)
                cmd += self._workers_flags(bf_task[wb].get('flags', {}))

                r_cmd = (''.join(str(x) + " " for x in cmd))
                r_sys = (''.join(str(x) + " " for x in system))
                self.blog.message("Executing: {}".format(r_sys + r_cmd), self._task_id,
                                  self.blog.msg)

                out, code = self._sys_adapter.execute(cmd, system, capture_out)
                return [out, code, r_sys + r_cmd, bf_task[wb].get('output')]

        except KeyError as e:
            msg = "Error while configuring workerBee specified " \
                  "tasks.\n{}".format(repr(e))
            self.blog.message(msg, self._task_id, self.blog.err)
            return [msg, 1, None, None]

    def _workers_containers(self, cont_conf, task_conf):
        """

        :param cont_conf:
        :param task_conf:
        :return:
        """
        name = task_conf['container'].get('name', next(iter(cont_conf)))
        cmd = ['ch-run']

        for f in cont_conf[name].get('defaultFlags', {}):
            self.__parse_dict(f, cmd)
        for f in task_conf['container'].get('flags', {}):
            self.__parse_dict(f, cmd)

        loc = self._input_mng.check_str(cont_conf[name].get('tarDir', '/var/tmp'))
        cmd.append(loc + "/" + self._input_mng.check_str(name))
        cmd.append("--")

        return cmd

    def _workers_system(self, sys):
        """

        :param sys:
        :return:
        """
        cmd = []

        if sys is not None:
            tar = sys.get('manageSys', self._manageSys)
            if tar == 'localhost':
                return cmd
            else:
                cmd.append(tar)
            for f in sys.get('flags', {}):
                self.__parse_dict(f, cmd)

        return cmd

    def _workers_flags(self, flags):
        """

        :param flags:
        :return:
        """
        cmd = []

        for f in flags:
            self.__parse_dict(f, cmd)

        return cmd

    def __parse_dict(self, f, cmd):
        """

        :param f:
        :param cmd:
        :return:
        """
        if isinstance(f, dict):
            for k, v in f.items():
                cmd.append(self._input_mng.check_str(k))
                if v is not None:
                    cmd.append(self._input_mng.check_str(v))
        else:
            cmd.append(self._input_mng.check_str(f))
