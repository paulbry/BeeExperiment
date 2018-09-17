# project
from .bee_cluster import BeeTask
from .orc_translator import Adapter
from bee_internal.shared_tools import GlobalMethods


class BeeLocalhostLauncher(BeeTask):
    def __init__(self, task_id, beefile, beelog, input_mng):
        BeeTask.__init__(self, task_id=task_id, beefile=beefile, beelog=beelog,
                         input_mng=input_mng)

        self._current_status = 10  # initializing
        self.begin_event = 0
        self.end_event = 0

        # task / configuration
        self.platform = 'BEE-Localhost'
        try:
            self._manageSys = self._beefile['requirements']['ResourceRequirement']\
                .get('manageSys', 'localhost')
        except KeyError:
            self._manageSys = 'localhost'

        # objects
        self._sys_adapter = Adapter(system=self._manageSys, config=self._beefile,
                                    file_loc='', task_name=self._task_id,
                                    beelog=self.blog, input_mng=self._input_mng)
        self._job_id = self._sys_adapter.get_jobid()
        self._remote = self._sys_adapter.get_remote_orc()
        self.global_m = GlobalMethods(beefile=self._beefile, task_name=self._task_id,
                                      beelog=self.blog, bldaemon=self._remote,
                                      job_id=self._job_id)

        self.current_status = 20  # initialized

    # Wait events (support for existing bee_orc_ctl)
    def add_wait_event(self, new_event):
        self.__event_list(new_event)

    # Task management
    def run(self):
        self.launch()

        self.begin_event = 1
        self._current_status = 50  # Running

        self.execute_workers()
        self.execute_base()

        self.end_event = 1
        self._current_status = 60  # finished

        if self._beefile.get('terminateAfter', True):
            self.terminate(clean=True)

    def launch(self):
        self._current_status = 40  # Launching
        # TODO: what else ???

    def execute_workers(self):
        for workers in self.global_m.fetch_bf_val(self._beefile, 'workerBees', [],
                                                  False, True, self._current_status):
            wb_type = (next(iter(workers))).lower()
            t_res = [None, -1, None, None]
            # t_res = [stdOut, exitStatus, command, outputTarget]
            if wb_type == 'task':
                for t in workers[next(iter(workers))]:
                    t_res = self._bee_tasks(t)
                    self.__handle_worker_result(t_res)
            elif wb_type == 'lambda':
                pass
            elif wb_type == 'subbee':
                # self._sub_bee(workers.get(wb, {}))
                pass
            else:
                out = "Unsupported workerBee detected: {}".format(workers)
                t_res[1] = 1
                self.blog.message(out, self._task_id, self.blog.err)

        self.terminate()

    def __handle_worker_result(self, result):
        if result[1] > 0:
            self.global_m.err_control(code=result[1], cmd=result[2], out=None,
                                      err=result[0], status=self.current_status,
                                      err_exit=False)
        else:  # code == 0
            self.global_m.out_control(cmd=result[2], out=result[0],
                                      status=self.current_status)
            if result[0] is not None and result[1] == 0 and result[3] is not None:
                self._input_mng.update_vars(result[3], result[0])

    def wait_for_others(self):
        self._current_status = 30  # Waiting
        for event in self.event_list:
            event.wait()

    def execute_base(self):
        cmd = self._input_mng.prepare_base_cmd(self._beefile.get('baseCommand'))
        if cmd is not None:
            out = self._sys_adapter.execute(cmd)

    def terminate(self, clean=False):
        if clean:
            self._current_status = 70  # Closed (clean)
        else:
            self._current_status = 80  # Terminate
        self.remote.shutdown_daemon()
