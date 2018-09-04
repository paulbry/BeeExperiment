# project
from .bee_cluster import BeeTask
from .orc_translator import Adapter


# Manipulates all nodes in a task
class BeeLocalhostLauncher(BeeTask):
    def __init__(self, task_id, beefile):
        BeeTask.__init__(self, task_id=task_id, beefile=beefile)

        self.__current_status = 0  # initializing
        self.begin_event = 0
        self.end_event = 0

        # Task configuration
        self.platform = 'BEE-Localhost'

        self._manageSys = self._beefile['requirements']['ResourceRequirement']\
            .get('manageSys', 'localhost')
        self._sys_adapter = Adapter(system="localhost", config=self._beefile,
                                    file_loc='', task_name=self._task_id)

        self.current_status = 1  # initialized

    # Wait events (support for existing bee_orc_ctl)
    def add_wait_event(self, new_event):
        self.__event_list(new_event)

    # Task management
    def run(self):
        self.launch()

        self.begin_event = 1
        self.__current_status = 4  # Running

        self.execute_workers()
        self.execute_base()

        self.end_event = 1

    def launch(self):
        self.terminate()
        self.__current_status = 3  # Launching
        # TODO: what else ???

    def execute_workers(self):
        # TODO: document and support for inputs / outputs
        # TODO: identify plan for support variables
        pass

    def execute_base(self):
        # TODO: document
        cmd = [self._beefile.get('baseCommand')]
        if cmd[0] is not None:
            # TODO: implement support for input/output
            self._sys_adapter.execute(cmd)

    def wait_for_others(self):
        self.current_status = 2  # Waiting
        for event in self.event_list:
            event.wait()
