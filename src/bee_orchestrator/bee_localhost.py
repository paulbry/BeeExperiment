# system
from termcolor import cprint
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
        pass
        # TODO: run worker bees

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

    # Task management support functions (private)
    def __fetch_beefile_value(self, key, dictionary, default=None, quit_err=False,
                              silent=False):
        """
        Fetch a specific key/value pair from the .beefile and
        raise error is no default supplied and nothing found
        :param key: Key for value in dictionary
        :param dictionary: dictionary to be searched
                            e.g. self.__beefile['task_conf']
        :param default: Returned if no value found, if None (def)
                        then error message surfaced
        :param quit_err: Exit with non-zero (default=False)
        :param silent: Hide warning message (default=False)
        :return: Value for key. Data type dependent on beefile,
                    and no verification beyond existence
        """
        try:
            return dictionary[key]
        except KeyError:
            if default is not None and not quit_err:
                if not silent:
                    cprint("[" + self._task_id + "] User defined value for ["
                           + str(key) + "] was not found, default value: "
                           + str(default) + " used.", self.warning_color)
                return default
            else:
                cprint("[" + self._task_id + "] Key: " + str(key) + " was not found in: " +
                       str(dictionary), self.error_color)
                exit(1)
