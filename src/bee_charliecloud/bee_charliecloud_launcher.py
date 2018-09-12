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
        self.__cc_default_key = list(self._beefile_req['CharliecloudRequirement'].keys())[0]
        self.__cc_flags = self.__default_flags()

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

        # TODO: re-implement
        """
        # Fill bee_cc_list of running hosts (nodes)
        # Each element is an BeeCharliecloudNode object
        for host in self.__hosts:
            curr_rank = len(self.__bee_cc_list)
            self.__hosts_mpi += str(host) + ","
            self.__hosts_total += 1
            if curr_rank == 0:
                hostname = "{}=bee-head".format(self.__task_name)
            else:
                hostname = "{}-bee-worker{}".format(self.__task_name,
                                                    str(curr_rank).zfill(3))
            # Each object represent a node
            bee_cc = BeeCharliecloudNode(task_id=self.__task_id, hostname=hostname,
                                     host=host, rank=curr_rank, task_conf=self.__task_conf,
                                     bee_cc_conf=self.__bee_charliecloud_conf,
                                     container_name=self.__container_name)
            # Add new CC to host
            self.__bee_cc_list.append(bee_cc)
            bee_cc.master = self.__bee_cc_list[0]

        # Remove erroneous comma (less impact), for readability
        if self.__hosts_mpi[-1] == ",":
            self.__hosts_mpi = self.__hosts_mpi[:-1]

        cprint("Preparing launch " + self._task_id + " for nodes "
               + self.__hosts_mpi, self.output_color)

        # Check if there is an allocation to unpack images on
        if 'SLURM_JOBID' in os.environ:
            cprint(os.environ['SLURM_NODELIST'] + ": Launching " +
                   str(self.__task_name), self.output_color)

            # use_existing (invoked via flag at runtime)
            # leverages an already existing unpacked image
            if not self.__use_existing:
                self.__unpack_ch_dir(self.__hosts_mpi, self.__hosts_total)
            self.wait_for_others()
            self.run_scripts()
        elif self.__hosts == ["localhost"]:  # single node or local instance
            cprint("Launching local instance " + str(self.__task_name),
                   self.output_color)
            self.__local_launch()
            self.run_scripts()
        else:
            cprint("[" + self.__task_name + "] No nodes allocated!", self.error_color)
            self.terminate()
        """

    def execute_workers(self):
        # TODO: document and support for inputs / outputs
        # TODO: identify plan for support variables
        workers = self._beefile.get('workerBees')
        if workers is not None:
            for wb in workers:
                cmd = ['ch-run']
                prog = workers[wb].get('program')
                if prog is not None:
                    p_sys = prog.get('system')
                    if p_sys is not None:
                        # TODO: verify system = container!
                        cmd += self.__cc_flags.get(p_sys)
                        p_sys = self._input_mng.check_str(p_sys)
                        cmd.append(str(p_sys))
                    p_flags = prog.get('flags')
                    if p_flags is not None:
                        for key, value in p_flags.items():
                            cmd.append(str(self._input_mng.check_str(key)))
                            if value is not None:
                                cmd.append((str(self._input_mng.check_str(value))))
                cmd.append("--")
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
        self.remove_cc_containers()
        self._bldaemon.shutdown_daemon()

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
