# system
import os
import socket
import _thread
import cProfile, pstats, io
from json import load, dumps
from pwd import getpwuid
from subprocess import Popen, CalledProcessError
from time import sleep, strftime, time
# 3rd party
import Pyro4
import Pyro4.naming
import Pyro4.errors
# project
from bee_internal.in_out_manage import InputManagement
from bee_logging.bee_log import BeeLogging
from bee_orchestrator.bee_cluster import BeeCluster


@Pyro4.expose
class BeeLauncherDaemon(object):
    def __init__(self, beelog, daemon=None, debug=False):
        self.debug = debug  # Manual test analysis
        if self.debug:
            self.cpr = cProfile.Profile()
            self.cpr.enable()

        self.beetask = None  # one task per instance of daemon!
        self.termination_lock = False
        self.orc_daemon = daemon
        self.blog = beelog  # Logging conf. object

        self.blog.message("Starting Bee orchestration controller..")

    def _create_task(self, beefile, file_name, input_mng):
        """
        Create a self.beetask (BeeCluster) object and assign to variable
        :param beefile: Dictionary object of beefile (beefile_manager)
        :param file_name: <file_name>.beefile
        :param input_mng: Object (InputManagement(...))
        """
        self.blog.message("Bee orchestration controller: received task "
                          "creating request")
        beetask_name = beefile.get('id', file_name + strftime("_%Y%m%d_%H%M%S"))
        self.blog.message("Launched BEE Instance!", task_name=beetask_name,)
        self.beetask = BeeCluster(beetask_name, beefile, self.blog, input_mng)

    def _launch_task(self):
        """
        Start task assigned as object variable
        """
        self.beetask.start()
    
    def create_and_launch_task(self, beefile, file_name, blog_args, mng_args):
        """
        :param beefile: Dictionary object of beefile (beefile_manager)
        :param file_name: <file_name>.beefile
        :param blog_args: dictionary for beelog related arguments
                (logflag: ?, log_dest: ?, quite: ?)
                Used to generated BeeLog object
        :param mng_args: dictionary of input management related arguments
                (user_values: ?, yml_file_name: ?)
                Used to generate InputMangement object
        """
        self.blog = BeeLogging(blog_args.get('logflag'), blog_args.get('log_dest'),
                               blog_args.get('quite'))
        self.blog.message("Task received in current working directory: " + os.getcwd(),
                          "{}.beefile".format(file_name), self.blog.msg)
        input_mng = InputManagement(beefile, mng_args.get('user_values'),
                                    self.blog, mng_args.get('yml_file_name'))
        self._create_task(beefile, file_name, input_mng)
        self._launch_task()

    ##############################################
    # terminate/delete/list could be better
    # suited in current implementation with
    # launcher; however, they need to be planned
    # in the daemon for other implementations
    ##############################################

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

            #TODO: continue rewrite to better support

    def shutdown_daemon(self):
        """
        Cleanly shutdown daemon, dump debug information if flag is True
        """
        self.blog.message("Bee orchestration controller shutting down",
                          color=self.blog.msg)

        # Manual test analysis
        if self.debug:
            self.cpr.disable()
            s = io.StringIO()
            sortby = 'cumulative'
            ps = pstats.Stats(self.cpr, stream=s).sort_stats(sortby)
            ps.print_stats()
            print(s.getvalue())

        self.orc_daemon.shutdown()


class ExecOrc(object):
    def __init__(self, beelog):
        self.blog = beelog

        # Parameters for Pyro4
        self.__open_port = self.__get_open_port()
        self.__hmac_key = getpwuid(os.getuid())[0]

        self.__update_system_conf()
        os.environ["PYRO_HMAC_KEY"] = self.__hmac_key

    def main(self, beefile=None, file_name=None, blog_args=None, mng_args=None,
             start=None, debug=False):
        """
        Prepare environment for daemon and launch (loop)
            https://pypi.org/project/Pyro4/
        """
        if self.__run_popen_bool(['python', '-m', 'Pyro4.naming', '-p',
                                  str(self.__open_port)]):

            ns = self.__get_name_server()
            daemon = Pyro4.Daemon()
            bldaemon = BeeLauncherDaemon(self.blog, daemon, debug)
            bldaemon_uri = daemon.register(bldaemon)
            ns.register("bee_launcher.daemon", bldaemon_uri)
            print(bldaemon_uri)
            self.blog.message("Bee orchestration controller started.",
                              color=self.blog.msg)
            if start is not None:
                end = time()
                self.blog.message("Orchestrator launch time: {0}".format(end-start))

            if blog_args is not None and mng_args is not None:
                # Launch beefile(s) passed at runtime in CLI
                # Checks for daemon in case the launch is delayed / slow
                _thread.start_new_thread(self.__delay_launch, ((beefile, file_name,
                                                                blog_args, mng_args,
                                                                bldaemon_uri, )))
            daemon.requestLoop()
        else:
            exit(1)

    @staticmethod
    def __delay_launch(beefile, file_name, blog_args, mng_args, bldaemon_uri):
        remote = Pyro4.Proxy(bldaemon_uri)
        remote.create_and_launch_task(beefile, file_name, blog_args, mng_args)

    def __get_name_server(self):
        """
        Return Pyro4 NS, will try until running
        ONLY invoke after NS process has been started
        :return: Located NS (Pyro4) object
        """
        ns = None
        while ns is None:
            try:
                ns = Pyro4.locateNS(port=self.__open_port, hmac_key=self.__hmac_key)
            except Pyro4.errors.CommunicationError:
                pass
            except Pyro4.errors.NamingError:
                pass
        return ns

    def __update_system_conf(self):
        """
        Create temp configuration file to store
        port used by NS for later reference
        """
        # conf_file = str(os.path.expanduser('~')) + "/.bee/port_conf.json"
        conf_file = "/var/tmp/.bee/port_conf.json"
        with open(conf_file, 'r+') as fc:
            data = load(fc)
            data["pyro4-ns-port"] = self.__open_port
            fc.seek(0)
            fc.write(dumps(data))
            fc.truncate()

    @staticmethod
    def __get_open_port():
        """
        :return: Unused port for use by NS
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port

    def __run_popen_bool(self, command):
        """
        Run command via Popen
        :param command:
        :return: boolean (t is successful)
        """
        try:
            Popen(command)
            return True
        except CalledProcessError as e:
            self.blog.message(msg="Error during - " + str(command) + "\n" +
                                  str(e), color=self.blog.err)
            return False
        except OSError as e:
            self.blog.message(msg="Error during - " + str(command) + "\n" +
                                  str(e), color=self.blog.err)
            return False
