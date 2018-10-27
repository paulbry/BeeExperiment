# system
import argparse
from json import load
from os import getuid
from pwd import getpwuid
from threading import Thread, Event
# 3rd party
import Pyro4
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
        self.node_list = []
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
        self._event_list = []

    ###########################################################################
    # Event/Trigger management
    ###########################################################################
    @property
    def begin_event(self):
        return self.__begin_event

    @begin_event.setter
    def begin_event(self, flag):
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
        if flag == 0:
            self.__end_event = Event()
        elif flag == 1:
            self.__end_event.set()
        else:
            self.__end_event.clear()

    @property
    def event_list(self):
        return self._event_list

    @event_list.setter
    def event_list(self, new_event):
        """
        Append event to event_list
        :param new_event:
        """
        self._event_list.append(new_event)

    ###########################################################################
    # Standard BEE methods
    ###########################################################################
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

    ###########################################################################
    # Task management support functions (private/protected)
    ###########################################################################
    @staticmethod
    def __pyro_port():
        """
        Return port used by daemon (Pyro4)
        """
        # conf_file = str(path.expanduser('~')) + "/.bee/port_conf.json"
        conf_file = "/var/tmp/.bee/port_conf.json"
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
    def _bee_cmd(self, cmd_task):
        """

        :param cmd_task:
        :return:
        """
        try:
            for wb in cmd_task:
                o_cmd = cmd_task[wb].get('cmd')
                cmd = []
                o_cfg = cmd_task[wb].get('output')

                if o_cmd is not None:
                    if o_cfg is not None:
                        capture_out = True
                    else:
                        capture_out = False

                    if isinstance(o_cmd, list):
                        for e in o_cmd:
                            cmd.append(self._input_mng.check_str(e))

                        r_cmd = (''.join(str(x) + " " for x in cmd))
                        self.blog.message("Executing: {}".format(r_cmd), self._task_id,
                                          self.blog.msg)

                        out, code = self._sys_adapter.execute(cmd, [], capture_out)
                        return [out, code, r_cmd, o_cfg]
                    else:
                        msg = "Command variable is not list"
                        self.blog(msg, self._task_id, self.blog.err)
                        return [msg, 1, str(cmd), None]
                else:
                    msg = "Unable to identify cmd key (command) for {}".format(wb)
                    self.blog.message(msg, self._task_id, self.blog.err)
                    return [msg, 1, None, None]
        except KeyError as e:
            msg = "Error while configuring workerBee specified " \
                  "command.\n{}".format(repr(e))
            self.blog.message(msg, self._task_id, self.blog.err)
            return [msg, 1, None, None]

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
                    # In order to support this I need to identify why it would occur
                    # and under what circumstances. Offline will imply we cannot move
                    # on with the current task until this sub "beetask" has bee completed.
                    # How will we manage this? what will we do if it doesnt?
                    # can we garuntee the ability to monitor across all possible systems?
                    self.blog.message("offline SubBee not supported yet!",
                                      color=self.blog.err)
                return result
        except KeyError as e:
            msg = "Error while configuring workerBee specified " \
                  "subBee.\n{}".format(repr(e))
            self.blog.message(msg, self._task_id, self.blog.err)
            return [msg, 1, None, None]

    ###########################################################################
    # WorkerBee TASK specif functions (protected)
    # goal, to ensure a consistent execution of all tasks
    # as decayed in the beefile. Will follow a logical approach of
    # system {flags} + container {flags} + task {flags} in building the
    # command that will be invoked.
    ###########################################################################
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
        cmd = []

        for f in flags:
            self.__parse_dict(f, cmd)

        return cmd

    def __parse_dict(self, f, cmd):
        """
        Examine flag (dict or string) from beefile that will be
        appened to cmd (command), will verify against input for
        potential templating requirement
        :param f: flag to be appended
        :param cmd: command [list] you wish flag to be appended too
        """
        if isinstance(f, dict):
            for k, v in f.items():
                cmd.append(self._input_mng.check_str(k))
                if v is not None:
                    cmd.append(self._input_mng.check_str(v))
        else:
            cmd.append(self._input_mng.check_str(f))
