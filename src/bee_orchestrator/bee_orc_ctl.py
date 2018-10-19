# system
import os
import socket
import _thread
from json import load, dumps
from pwd import getpwuid
from subprocess import Popen
from time import sleep, strftime
# 3rd party
import Pyro4
import Pyro4.naming
# project
from bee_internal.in_out_manage import InputManagement
from bee_logging.bee_log import BeeLogging
from bee_orchestrator.bee_cluster import BeeCluster


@Pyro4.expose
class BeeLauncherDaemon(object):
    def __init__(self, beelog, daemon=None):
        self.blog = beelog  # Logging conf. object

        self.blog.message("Starting Bee orchestration controller..")
        self.__py_dir = os.path.dirname(os.path.abspath(__file__))
        self.beetask = None
        self.orc_daemon = daemon
        self.termination_lock = False

    def create_task(self, beefile, file_name, input_mng):
        self.blog.message("Bee orchestration controller: received task "
                          "creating request")
        beetask_name = beefile.get('id', file_name + strftime("_%Y%m%d_%H%M%S"))
        self.blog.message("Launched BEE Instance!", task_name=beetask_name,)
        self.beetask = BeeCluster(beetask_name, beefile, self.blog, input_mng)

    def launch_task(self):
        self.beetask.start()
    
    def create_and_launch_task(self, beefile, file_name, blog_args, mng_args):
        self.blog = BeeLogging(blog_args.get('logflag'), blog_args.get('log_dest'),
                               blog_args.get('quite'))
        self.blog.message("Task received in current working directory: " + os.getcwd(),
                          "{}.beefile".format(file_name), self.blog.msg)
        input_mng = InputManagement(beefile, mng_args.get('user_values'),
                                    self.blog, mng_args.get('yml_file_name'))
        self.create_task(beefile, file_name, input_mng)
        self.launch_task()

    def terminate_task(self, beetask_name):
        pass

    def delete_task(self, beetask_name):
        pass

    def list_all_tasks(self):
        pass

    def launch_internal_beeflow(self, beeflow, beefile_list, parent_beefile,
                                node_list, flow_name):
        self.blog.message("Internal BeeFlow triggered", flow_name, color=self.blog.msg)

        # Initialize each task
        beeflow_tasks = {}
        nodes_used = 0

        for task_name in beefile_list:
            beefile = beefile_list[task_name]
            try:
                num_n = int(beefile['requirements']['ResourceRequirement'].get('numNodes', 1))
                msys = beefile['requirements']['ResourceRequirement'].get('manageSys')
                if msys != 'slurm':
                    print("ERROR: only slurm supported for internal BeeFlow at this time!")
                    exit(1)
                if num_n + nodes_used > len(node_list):
                    print("ERROR more nodes requested than available!")
                    exit(1)
                hosts = None
                for i in range(0, num_n):
                    print(node_list[i + nodes_used])
                    if hosts is None:
                        hosts = str(node_list[i + nodes_used])
                    else:
                        hosts += ".{}".format(node_list[i + nodes_used])
                nodes_used += num_n
                beefile['requirements']['ResourceRequirement'].update({'nodeList': hosts})

                if parent_beefile['requirements'].get('CharliecloudRequirement') is not None:
                    print(parent_beefile['requirements'].get('CharliecloudRequirement'))
                    beefile['requirements'].update(
                        {'CharliecloudRequirement': parent_beefile['requirements'].get('CharliecloudRequirement')})
            except KeyError as err:
                print("ERROR: incorrect beefile configuration\n{}".format(err))
                exit(1)
            # beefile.update({'requirements': {'ResourceRequirement': {'nodeList': 'test'}}})
            print(beefile)
            # beetask = self.create_task(beefile)
            beetask = "OBJECT"
            beeflow_tasks.update({task_name: beetask})
            # self.__beetasks[task_name] = beetask

    def shutdown_daemon(self):
        self.blog.message("Bee orchestration controller shutting down",
                          color=self.blog.msg)
        self.orc_daemon.shutdown()


class ExecOrc(object):
    def __init__(self, beelog):
        self.blog = beelog

    def main(self, beefile=None, file_name=None, blog_args=None, mng_args=None):
        """
        Prepare environment for daemon and launch (loop)
            https://pypi.org/project/Pyro4/
        """
        #############################################################
        # TODO: document daemon!!!
        #############################################################
        open_port = self.get_open_port()
        self.update_system_conf(open_port)
        hmac_key = getpwuid(os.getuid())[0]
        os.environ["PYRO_HMAC_KEY"] = hmac_key
        Popen(['python', '-m', 'Pyro4.naming', '-p', str(open_port)])
        sleep(5)
        daemon = Pyro4.Daemon()
        bldaemon = BeeLauncherDaemon(self.blog, daemon)
        bldaemon_uri = daemon.register(bldaemon)
        ns = Pyro4.locateNS(port=open_port, hmac_key=hmac_key)
        ns.register("bee_launcher.daemon", bldaemon_uri)
        print(bldaemon_uri)
        self.blog.message("Bee orchestration controller started.",
                          color=self.blog.msg)
        if blog_args is not None and mng_args is not None:
            # TODO: implement better solution (possibly in __main__)?
            _thread.start_new_thread(self.delay_launch, ((beefile, file_name,
                                                          blog_args, mng_args,
                                                          bldaemon_uri, )))
        daemon.requestLoop()

    @staticmethod
    def delay_launch(beefile, file_name, blog_args, mng_args, bldaemon_uri):
        sleep(4)
        remote = Pyro4.Proxy(bldaemon_uri)
        remote.create_and_launch_task(beefile, file_name, blog_args, mng_args)

    @staticmethod
    def update_system_conf(open_port):
        # conf_file = str(os.path.expanduser('~')) + "/.bee/port_conf.json"
        conf_file = "/var/tmp/.bee/port_conf.json"
        with open(conf_file, 'r+') as fc:
            data = load(fc)
            data["pyro4-ns-port"] = open_port
            fc.seek(0)
            fc.write(dumps(data))
            fc.truncate()

    @staticmethod
    def get_open_port():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("", 0))
            s.listen(1)
            port = s.getsockname()[1]
            s.close()
            return port
