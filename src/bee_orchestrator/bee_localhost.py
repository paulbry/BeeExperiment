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
        for workers in self._g_share.fetch_bf_val(self._beefile, 'workerBees', {},
                                                  False, True):
            for wb in workers:
                if wb.lower() == 'task':
                    self._bee_tasks(workers.get(wb, {}), self._beefile_req['CharliecloudRequirement'])
                elif wb.lower() == 'lambda':
                    pass
                elif wb.lower() == 'subbee':
                    pass
                else:
                    self.blog.message("Unsupported workerBee detected: {}".format(wb),
                                      self._task_id, self.blog.err)

    def wait_for_others(self):
        self.__current_status = 30  # Waiting
        for event in self.event_list:
            event.wait()

    def execute_base(self):
        cmd = self._input_mng.prepare_base_cmd(self._beefile.get('baseCommand'))
        if cmd is not None:
            out = self._sys_adapter.execute(cmd)

    def terminate(self, clean=False):
        if clean:
            self.__current_status = 70  # Closed (clean)
        else:
            self.__current_status = 80  # Terminate
        self.remote.shutdown_daemon()
