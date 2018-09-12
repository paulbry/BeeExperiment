# project
from .bee_cluster import BeeTask
from .orc_translator import Adapter


class BeeLocalhostLauncher(BeeTask):
    def __init__(self, task_id, beefile, beelog, input_mng):
        BeeTask.__init__(self, task_id=task_id, beefile=beefile, beelog=beelog,
                         input_mng=input_mng)

        self.__current_status = 10  # initializing
        self.begin_event = 0
        self.end_event = 0

        # Task configuration
        self.platform = 'BEE-Localhost'

        try:
            self._manageSys = self._beefile['requirements']['ResourceRequirement']\
                .get('manageSys', 'localhost')
        except KeyError:
            self._manageSys = 'localhost'
        self._sys_adapter = Adapter(system=self._manageSys, config=self._beefile,
                                    file_loc='', task_name=self._task_id,
                                    beelog=self.blog, input_mng=self._input_mng)

        self.current_status = 20  # initialized

    # Wait events (support for existing bee_orc_ctl)
    def add_wait_event(self, new_event):
        self.__event_list(new_event)

    # Task management
    def run(self):
        self.launch()

        self.begin_event = 1
        self.__current_status = 50  # Running

        self.execute_workers()
        self.execute_base()

        self.end_event = 1
        self.__current_status = 60  # finished

        if self._beefile.get('terminateAfter', True):
            self.terminate(clean=True)

    def launch(self):
        self.__current_status = 40  # Launching
        # TODO: what else ???

    def execute_workers(self):
        # TODO: document and support for inputs / outputs
        # TODO: identify plan for support variables
        workers = self._beefile.get('workerBees')
        if workers is not None:
            for wb in workers:
                cmd = []
                prog = workers[wb].get('program')
                if prog is not None:
                    p_sys = prog.get('system')
                    if p_sys is not None:
                        p_sys = self._input_mng.check_str(p_sys)
                        cmd.append(str(p_sys))

                    p_flags = prog.get('flags')
                    if p_flags is not None:
                        for key, value in p_flags.items():
                            cmd.append(str(self._input_mng.check_str(key)))
                            if value is not None:
                                cmd.append((str(self._input_mng.check_str(value))))

                cmd.append(str(self._input_mng.check_str(wb)))

                wb_flags = workers[wb].get('flags')
                if wb_flags is not None:
                    for key, value in wb_flags.items():
                        cmd.append(str(self._input_mng.check_str(key)))
                        if value is not None:
                            cmd.append((str(self._input_mng.check_str(value))))

                self.blog.message("Executing: " + str(cmd), self._task_id,
                                  self.blog.msg)
                out = self._sys_adapter.execute(cmd, system=prog)
                if out is not None and workers[wb].get('output') is not None:
                    self._input_mng.update_vars(workers[wb].get('output'), out)

    def wait_for_others(self):
        self.__current_status = 30  # Waiting
        for event in self.event_list:
            event.wait()

    def execute_base(self):
        # TODO: support output in accordance with OWL
        cmd = self._input_mng.prepare_base_cmd(self._beefile.get('baseCommand'))
        if cmd is not None:
            out = self._sys_adapter.execute(cmd)

    def terminate(self, clean=False):
        if clean:
            self.__current_status = 70  # Closed (clean)
        else:
            self.__current_status = 80  # Terminate
        self._bldaemon.shutdown_daemon()
