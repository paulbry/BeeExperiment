class BeeNode(object):
    def __init__(self, task_id, hostname, host, beefile,
                 beelog, shared_dir=None, user_name="beeuser"):
        # Logging conf. object -> BeeLogging(log, log_dest, quite)
        self.blog = beelog

        # Basic configurations
        self.__status = ""
        self.__hostname = hostname
        self.master = ""
        self._node = host

        # Job configuration
        self.task_id = task_id
        self._beefile = beefile

        # Shared resourced
        self.shared_dir = shared_dir
        self.user_name = user_name

    @property
    def hostname(self):
        return self.__hostname

    @hostname.setter
    def hostname(self, h):
        self.blog.message("Setting hostname to " + h,
                          self.__hostname, self.blog.msg)
        cmd = ["hostname", self.__hostname]
        # self.gen.run_popen_safe(command=cmd)

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, status):
        self.blog.message("Setting status",
                          self.__hostname, self.blog.msg)
        self.__status = status

    # Bee launching / management related functions
    def start(self):
        self.blog.message("\tBeeNode starting via host: {}".format(self._node),
                          self.hostname)

    def checkpoint(self):
        pass

    def restore(self):
        pass

    def kill(self):
        pass
