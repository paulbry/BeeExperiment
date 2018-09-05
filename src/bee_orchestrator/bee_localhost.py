# project
from .bee_cluster import BeeTask
from .orc_translator import Adapter


# Manipulates all nodes in a task
class BeeLocalhostLauncher(BeeTask):
    def __init__(self, task_id, beefile):
        BeeTask.__init__(self, task_id=task_id, beefile=beefile)

        self.__current_status = 10  # initializing
        self.begin_event = 0
        self.end_event = 0

        # Task configuration
        self.platform = 'BEE-Localhost'

        self._manageSys = self._beefile['requirements']['ResourceRequirement']\
            .get('manageSys', 'localhost')
        self._sys_adapter = Adapter(system="localhost", config=self._beefile,
                                    file_loc='', task_name=self._task_id)

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

    def launch(self):
        self.terminate()
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
                        cmd.append(str(p_sys))

                    p_flags = prog.get('flags')
                    if p_flags is not None:
                        for key, value in p_flags.items():
                            cmd.append(str(key))
                            if value is not None:
                                cmd.append((str(value)))

                cmd.append(str(wb))

                wb_flags = workers[wb].get('flags')
                if wb_flags is not None:
                    for key, value in wb_flags.items():
                        cmd.append(str(key))
                        if value is not None:
                            cmd.append((str(value)))

                self._handle_message("[" + self._task_id + "] Executing: " + str(cmd),
                                     self._output_color)
                self._sys_adapter.execute(cmd, system=prog)

    def execute_base(self):
        # TODO: document
        cmd = [self._beefile.get('baseCommand')]
        if cmd[0] is not None:
            # TODO: implement support for input/output
            self._sys_adapter.execute(cmd)

    def wait_for_others(self):
        self.__current_status = 30  # Waiting
        for event in self.event_list:
            event.wait()

    def terminate(self, clean=False):
        if clean:
            self.__current_status = 70  # Closed (clean)
        else:
            self.__current_status = 80  # Terminate
        # TODO: review ways to manage/surpress error messages
        self._bldaemon.shutdown_daemon()
