# system
import os
import socket
import Pyro4
import Pyro4.naming
import time
from json import load, dumps
from pwd import getpwuid
from subprocess import Popen
from time import sleep
# project
from .bee_localhost import BeeLocalhostLauncher as beeLH


@Pyro4.expose
class BeeLauncherDaemon(object):
    def __init__(self, beelog, daemon=None):
        # Logging conf. object -> BeeLogging(log, log_dest, quite)
        self.blog = beelog

        self.blog.message("Starting Bee orchestration controller..")
        self.__py_dir = os.path.dirname(os.path.abspath(__file__))
        self.beetask = None
        self.orc_daemon = daemon

    def create_task(self, beefile, file_name):
        self.blog.message("Bee orchestration controller: received task "
                          "creating request")
        exec_target = beefile.get('class', 'bee-localhost')
        beetask_name = beefile.get('id', file_name + time.strftime("_%Y%m%d_%H%M%S"))
        # TODO: correct, accouting for optional/unavailable modules?
        if str(exec_target).lower() == 'bee-charliecloud':
            pass
        #    from exec_targets.bee_charliecloud.bee_charliecloud_launcher import \
        #        BeeCharliecloudLauncher as beeCC
        #    cprint("[" + beetask_name + "] Launched BEE-Charliecloud Instance!")
        #    self.beetask = beeCC(beetask_name, beefile)
        elif str(exec_target).lower() == 'bee-localhost':
            self.blog.message("Launched BEE-Localhost Instance!", task_name=beetask_name)
            self.beetask = beeLH(beetask_name, beefile, self.blog)

    def launch_task(self):
        self.beetask.start()
    
    def create_and_launch_task(self, beefile, file_name):
        self.blog.message("Task received in current working directory: " + os.getcwd(),
                          "{}.beefile".format(file_name), self.blog.msg)
        # TODO: add encode step for file!
        self.create_task(beefile, file_name)
        self.launch_task()

    def terminate_task(self, beetask_name):
        pass

    def delete_task(self, beetask_name):
        pass

    def list_all_tasks(self):
        pass

    def shutdown_daemon(self):
        self.blog.message("Bee orchestration controller shutting down",
                          color=self.blog.msg)
        self.orc_daemon.shutdown()


class ExecOrc(object):
    # TODO: identify class objects and update
    def __init__(self, beelog):
        self.blog = beelog

    def main(self, beefile=None, file_name=None):
        """
        Prepare environment for daemon and launch (loop)
            https://pypi.org/project/Pyro4/
        :param beefile: Task to be launched once daemon launched
                        Full path to task (beefile) e.g. /var/tmp/test
        :param file_name: Beefile name (no .beefile)
        """
        open_port = self.get_open_port()
        self.update_system_conf(open_port)
        hmac_key = getpwuid(os.getuid())[0]
        os.environ["PYRO_HMAC_KEY"] = hmac_key
        Popen(['python', '-m', 'Pyro4.naming', '-p', str(open_port)])
        sleep(5)
        #############################################################
        # TODO: document daemon!!!
        #############################################################
        daemon = Pyro4.Daemon()
        bldaemon = BeeLauncherDaemon(self.blog, daemon)
        bldaemon_uri = daemon.register(bldaemon)
        ns = Pyro4.locateNS(port=open_port, hmac_key=hmac_key)
        ns.register("bee_launcher.daemon", bldaemon_uri)
        self.blog.message("Bee orchestration controller started.",
                          color=self.blog.msg)

        # Launch task before starting daemon
        if beefile is not None:
            bldaemon.create_and_launch_task(beefile, file_name)

        daemon.requestLoop()

    @staticmethod
    def update_system_conf(open_port):
        conf_file = str(os.path.expanduser('~')) + "/.bee/port_conf.json"
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
