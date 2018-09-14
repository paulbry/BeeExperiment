# project
from bee_orchestrator.bee_cluster import BeeTask
from bee_orchestrator.orc_translator import Adapter


# Manipulates all nodes in a task
class BeeCharliecloudLauncher(BeeTask):
    def __init__(self, task_id, beefile, beelog, input_mng):
        BeeTask.__init__(self, task_id=task_id, beefile=beefile, beelog=beelog,
                         input_mng=input_mng)

        self.__current_status = 10  # initializing
        self.begin_event = 0
        self.end_event = 0

        # Task configuration
        self.platform = 'BEE-Charliecloud'

        try:
            self._manageSys = self._beefile['requirements']['ResourceRequirement']\
                .get('manageSys', 'localhost')
        except KeyError:
            self._manageSys = 'localhost'
        self._sys_adapter = Adapter(system=self._manageSys, config=self._beefile,
                                    file_loc='', task_name=self._task_id,
                                    beelog=self.blog, input_mng=self._input_mng)

        # DEFAULT Container configuration
        # TODO: add verification steps?
        self.__default_tar_dir = "/var/tmp"

        # bee-charliecloud
        self.__bee_cc_list = []

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

        self.blog.message("Charliecloud launching", self._task_id,
                          self.blog.msg)

        # TODO: re-implement self.__bee_cc_list

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
        # TODO: support output in accordance with OWL
        cmd = self._input_mng.prepare_base_cmd(self._beefile.get('baseCommand'))
        if cmd is not None:
            out = self._sys_adapter.execute(cmd)

    def terminate(self, clean=False):
        if clean:
            self.__current_status = 70  # Closed (clean)
        else:
            self.__current_status = 80  # Terminate
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
