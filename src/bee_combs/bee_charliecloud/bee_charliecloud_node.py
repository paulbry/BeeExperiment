# project
from bee_orchestrator.bee_node import BeeNode
from bee_internal.shared_tools import GeneralMethods


# functions and operations focused on a single node
class BeeCharliecloudNode(BeeNode):
    def __init__(self, task_id, hostname, host, rank, task_conf,
                 container_name, beelog):
        BeeNode.__init__(self, task_id=task_id, hostname=hostname, host=host,
                         rank=rank, task_conf=task_conf, beelog=beelog)

        # Node currently running on (for ease of use)
        self.__node = host

        # Charliecloud node configuration
        self.__container_name = container_name

        self.gen_m = GeneralMethods(self.blog)

    def general_run(self, script_path):
        """
        Override base general_run in order to implement module work around.
        Load Charliecloud prior to running the script...
        """
        cmd = ['sh', script_path]
        self.blog.message("General run: {}".format(cmd),
                          self.__node, self.blog.msg)
        self.gen_m.run_popen_safe(cmd)
