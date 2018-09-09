# system
from os import path
# project
from bee_internal.beefile_manager import BeefileLoader
from bee_internal.shared_tools import GeneralMethods
from bee_monitor.db_launch import LaunchDB
from .launcher_translator import Adapter
from bee_logging.bee_log import BeeLogging


class BeeLauncher(object):
    def __init__(self, log=False, log_dest="None", quite=False):
        # Logging configuration object
        self.blog = BeeLogging(log, log_dest, quite)

        self.gen = GeneralMethods(self.blog)
        self.__homedir = path.expanduser('~')

        # Database Tracking
        # TODO: implemented options bee_conf file?
        self._db_full = self.__homedir + "/.bee/launcher.db"

    def launch(self, beefile, task_name, file_loc, test_only=False):
        b_class = self.gen.fetch_bf_val(dictionary=beefile, key="class",
                                        quit_err=True)
        try:
            b_rjms = beefile['requirements']['ResourceRequirement']['manageSys']
        except KeyError:
            b_rjms = "localhost"

        self.blog.message("Preparing to launch..." +
                          "\n\tClass: " + str(b_class) + "\n\tRJMS: " + str(b_rjms),
                          task_name, self.blog.msg)
        adapt = Adapter(system=b_rjms, config=beefile, file_loc=file_loc,
                        task_name=task_name, beelog=self.blog)
        out = adapt.allocate(test_only=test_only)

        if out is not None:
            self.blog.message("[" + str(task_name) + "] launched with job id: "
                              + str(out), color=self.blog.msg)

            # Database / logging
            ldb = LaunchDB(self._db_full, self.blog)
            ldb.new_launch(job_id=out, b_class=b_class, b_rjms=b_rjms,
                           status="Launched", beefile_full=beefile,
                           beefile_loc=file_loc)
        else:
            self.blog.message("Test launch complete!", task_name,
                              self.blog.msg)

    def terminate_task(self, job_id, rjms):
        adapt = Adapter(system=rjms, config=None, file_loc=None, task_name=None,
                        beelog=self.blog)
        adapt.shutdown(job_id)


# Manage main argument responses
class BeeArguments(BeeLauncher):
    def __init__(self, log, log_dest, quite):
        BeeLauncher.__init__(self, log, log_dest, quite)

    def opt_launch(self, args):
        """
        Send launch request for single task to daemon
        :param args: command line argument namespace
        """
        beefile = str(args.launch_task[0])
        f = BeefileLoader(beefile, self.blog)
        self.launch(beefile=f.beefile, task_name=beefile,
                    file_loc=path.dirname(path.abspath("{}.beefile".format
                                                       (beefile))),
                    test_only=args.testonly)

    def opt_terminate(self, args):
        """
        Send termination request for specific task to daemon
        :param args: command line argument namespace
        """
        job_id = args.terminate_task[0]
        print("Sending termination request.")
        db = LaunchDB(db_location=self._db_full,
                      beelog=self.blog)
        rjms = db.query_value("jobID", job_id, "manageSys")
        if rjms is not None:
            self.terminate_task(job_id, rjms)
        else:
            self.blog.message("No task identified with JobID: {}".format(job_id),
                              color=self.blog.err)
        self.blog.message("Task: " + job_id + " is terminated.",
                          color=self.blog.msg)

    # TODO: implement high level status support using job id
    def opt_status(self):
        pass
