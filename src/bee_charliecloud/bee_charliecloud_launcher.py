# project
from bee_orchestrator.bee_cluster import BeeTask
from bee_orchestrator.orc_translator import Adapter
from bee_internal.shared_tools import GlobalMethods


# Manipulates all nodes in a task
class BeeCharliecloudLauncher(BeeTask):
    def __init__(self, task_id, beefile, beelog, input_mng):
        BeeTask.__init__(self, task_id=task_id, beefile=beefile, beelog=beelog,
                         input_mng=input_mng)

        self._current_status = 10  # initializing
        self.begin_event = 0
        self.end_event = 0

        # task / configuration
        self.platform = 'BEE-Charliecloud'
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

        # DEFAULT Container configuration
        # TODO: add verification steps?
        self.__default_tar_dir = "/var/tmp"
        self.bee_cc_list = []

        self._status_change(20)  # initialized

    # Wait events (support for existing bee_orc_ctl)
    def add_wait_event(self, new_event):
        self.__event_list(new_event)

    # Task management
    def run(self):
        self.launch()

        self.begin_event = 1
        self._status_change(50)  # Running

        self.execute_workers()
        self.execute_base()

        self.end_event = 1
        self._status_change(60)  # finished

        if self._beefile.get('terminateAfter', True):
            self.terminate(clean=True)

    def launch(self):
        self._status_change(40)  # Launching
        self.blog.message("Charliecloud launching", self._task_id,
                          self.blog.msg)
        # TODO: re-implement self.__bee_cc_list

    def execute_workers(self):
        for workers in self.global_m.fetch_bf_val(self._beefile, 'workerBees', [],
                                                  False, True, self._current_status):
            wb_type = (next(iter(workers))).lower()
            t_res = [None, -1, None, None]
            # t_res = [stdOut, exitStatus, command, outputTarget]
            if wb_type == 'task':
                for t in workers[next(iter(workers))]:
                    t_res = self._bee_tasks(t, self._beefile_req.get(
                        'CharliecloudRequirement'))
                    self.__handle_worker_result(t_res)
            elif wb_type == 'lambda':
                pass
            elif wb_type == 'subbee':
                for t in workers[next(iter(workers))]:
                    t_res = self._sub_bees(t)
                    self.__handle_worker_result(t_res)
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
        self._status_change(30)  # Waiting
        for event in self.event_list:
            event.wait()

    def execute_base(self):
        # TODO: support output in accordance with OWL
        cmd = self._input_mng.prepare_base_cmd(self._beefile.get('baseCommand'))
        if cmd is not None:
            out, code = self._sys_adapter.execute(cmd, None, False)

    def terminate(self, clean=False):
        if clean:
            self._status_change(70)  # Closed (clean)
        else:
            self._status_change(80)  # Terminate
        self.remove_cc_containers()
        self.remote.shutdown_daemon()

    # Task management support functions (private)
    def remove_cc_containers(self):
        for key, value in self._beefile_req.get('CharliecloudRequirement').items():
            if value.get('deleteAfter', False):
                tar_dir = value.get('tarDir')
                if tar_dir is None:
                    tar_dir = self.__default_tar_dir
                self.__remove_ch_dir(tar_dir, key)

    def __remove_ch_dir(self, ch_dir, ch_name):
        self.blog.message(msg="Removing Charliecloud container {}".format(ch_name),
                          task_name=self._task_id, color=self.blog.msg)
        cmd = ['rm', '-rf', ch_dir + "/" + ch_name]
        self._sys_adapter.execute(cmd)

    def __default_flags(self):
        tmp = {}
        for key, value in self._beefile_req.get('CharliecloudRequirement').items():
            flags = []
            for dfk, dfv in value.get('defaultFlags').items():
                flags.append(self._input_mng.check_str(dfk))
                if dfv is not None:
                    flags.append(self._input_mng.check_str(dfv))
            tmp.update({key: flags})
        return tmp
