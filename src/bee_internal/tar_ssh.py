class SSHAdaptee:
    def __init__(self, config, file_loc, task_name, beelog):
        self._config = config
        self._config_req = self._config['requirements']
        self._file_loc = file_loc
        self._task_name = task_name
        self._encode = 'UTF-8'

        # Logging conf. object -> BeeLogging(log, log_dest, quite)
        self.blog = beelog

    def specific_allocate(self, test_only=False):
        pass

    def specific_schedule(self):
        pass

    def specific_shutdown(self):
        pass

    def specific_move_file(self):
        pass

    def specific_execute(self):
        pass
