# project
from bee_orchestrator.bee_node import BeeNode


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
