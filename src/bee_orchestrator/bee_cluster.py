# system
import getpass
# project
from bee_orchestrator.bee_task import BeeTask
from bee_orchestrator.orc_translator import Adapter
from bee_internal.shared_tools import GlobalMethods
from bee_orchestrator.bee_node import BeeNode
from bee_internal.beefile_manager import BeefileLoader, BeeflowLoader


class BeeCluster(BeeTask):
    def __init__(self, task_id, beefile, beelog, input_mng):
        BeeTask.__init__(self, task_id=task_id, beefile=beefile, beelog=beelog,
                         input_mng=input_mng)

        self._current_status = 10  # initializing
        self.begin_event = 0
        self.end_event = 0

        # task / configuration
        try:
            self._manageSys = self._beefile['requirements']['ResourceRequirement']\
                .get('manageSys', 'localhost')
        except KeyError:
            self._manageSys = 'localhost'

        # Adapter (translator)
        self._sys_adapter = Adapter(system=self._manageSys, config=self._beefile,
                                    file_loc='', task_name=self._task_id,
                                    beelog=self.blog, input_mng=self._input_mng)
        self._job_id = self._sys_adapter.get_jobid()
        self._remote = self._sys_adapter.get_remote_orc()

        self.global_m = GlobalMethods(beefile=self._beefile, task_name=self._task_id,
                                      beelog=self.blog, bldaemon=self._remote,
                                      job_id=self._job_id)

        # DEFAULT Container configuration
        self.__default_tar_dir = "/var/tmp"
        self.node_list = self._sys_adapter.get_nodes()
        self.running_nodes = []

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
        self.blog.message("Launching", self._task_id,
                          self.blog.msg)
        self._sys_adapter.launch()

        self.blog.message("Generating node list", self._task_id,
                          self.blog.msg)
        for i in range(0, len(self.node_list)):
            if i == 0:
                hostname = "{}-{}-bee-master".format(getpass.getuser(),
                                                     self._task_id)
            else:
                hostname = "{}-{}-bee-worker{}".format(getpass.getuser(),
                                                       self._task_id, str(i).zfill(3))

            node = BeeNode(task_id=self._task_id, hostname=hostname,
                           host=self.node_list[i], beefile=self._beefile,
                           beelog=self.blog)
            node.start()
            self.running_nodes.append(node)

    def execute_workers(self):
        for workers in self.global_m.fetch_bf_val(self._beefile, 'workerBees', [],
                                                  False, True, self._current_status):
            wb_type = (next(iter(workers))).lower()
            t_res = [None, -1, None, None]
            ###################################################################
            # t_res = [stdOut, exitStatus, command, outputTarget]
            #   stdOut -> capture output only if required by beefile
            #   exitStatus -> code
            #   command -> string (join...) of command ran
            #   outputTarget -> variable in input_mng to be updated
            ###################################################################
            if wb_type == 'task':
                for t in workers[next(iter(workers))]:
                    t_res = self._bee_tasks(t, self._beefile_req.get(
                        'CharliecloudRequirement'))
                    self.__handle_worker_result(t_res)
            elif wb_type == 'subbee':
                for t in workers[next(iter(workers))]:
                    t_res = self._sub_bees(t)
                    self.__handle_worker_result(t_res)
            elif wb_type == 'command':
                for t in workers[next(iter(workers))]:
                    t_res = self._bee_cmd(t)
                    print(t_res)
                    self.__handle_worker_result(t_res)
            elif wb_type == 'internalflow':
                bflow = (BeeflowLoader(workers.get('InternalFlow'), self.blog)).beeflow
                bfiles = {}
                node_list = self._sys_adapter.get_nodes()
                for task in bflow:
                    bfiles.update({task: (BeefileLoader(task, self.blog)).beefile})
                self.remote.launch_internal_beeflow(beeflow=bflow,
                                                    beefile_list=bfiles,
                                                    parent_beefile=self._beefile,
                                                    node_list=node_list,
                                                    flow_name=workers.get('InternalFlow'))
            else:
                out = "Unsupported workerBee detected: {}".format(workers)
                t_res[1] = 1
                self.blog.message(out, self._task_id, self.blog.err)

    def wait_for_others(self):
        self._status_change(30)  # Waiting
        for event in self.event_list:
            event.wait()

    def execute_base(self):
        res, cmd = self._input_mng.prepare_base_cmd(self._beefile.get('baseCommand'))
        if res:
            out, code = self._sys_adapter.execute(cmd, None, False)
            self.__handle_worker_result([out, code, (''.join(str(x) + " " for x in cmd)),
                                         None])

    def terminate(self, clean=False):
        if clean:
            self._status_change(70)  # Closed (clean)
        else:
            self._status_change(80)  # Terminate
        self.remove_cc_containers()
        self.remote.shutdown_daemon()

    ############################################################################
    # Task management support functions (private)
    ############################################################################
    def remove_cc_containers(self):
        for key, value in self._beefile_req.get('CharliecloudRequirement', {}).items():
            if value.get('deleteAfter', False):
                tar_dir = value.get('tarDir')
                if tar_dir is None:
                    tar_dir = self.__default_tar_dir
                self.__remove_ch_dir(tar_dir, key)

    def __remove_ch_dir(self, ch_dir, ch_name):
        self.blog.message(msg="Removing Charliecloud container {}".format(ch_name),
                          task_name=self._task_id, color=self.blog.msg)
        cmd = ['rm', '-rf', ch_dir + "/" + ch_name]
        out, code = self._sys_adapter.execute(cmd, None, False)
        self.__handle_worker_result([out, code, (''.join(str(x) + " " for x in cmd)),
                                     None])

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

    def __handle_worker_result(self, result):
        """
        Manage results list and ensure details are allocated
        :param result: t_res (see execute_workers)
            [stdOut, exitStatus, command, outputTarget]
        """
        if result[1] != 0:
            self.global_m.err_control(code=result[1], cmd=result[2], out=None,
                                      err=result[0], status=self.current_status,
                                      err_exit=False)
        else:  # code == 0
            self.global_m.out_control(cmd=result[2], out=result[0],
                                      status=self.current_status)
            if result[0] is not None and result[1] == 0 and result[3] is not None:
                self._input_mng.update_vars(result[3], result[0])
