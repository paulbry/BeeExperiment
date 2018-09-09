# system
from os import path
# project
from bee_internal.beefile_manager import BeefileLoader, BeefileExamine, \
    YMLLoader
from bee_internal.shared_tools import GeneralMethods
from bee_monitor.db_launch import LaunchDB
from .launcher_translator import Adapter


class BeeLauncher(object):
    def __init__(self, beelog):
        # Logging configuration object
        self.blog = beelog

        self.gen = GeneralMethods(self.blog)
        self.__homedir = path.expanduser('~')

        # Database Tracking
        # TODO: implemented options bee_conf file?
        self._db_full = self.__homedir + "/.bee/launcher.db"

    def launch(self, beefile, task_name, file_loc, test_only=False,
               yml_in_file=None):
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
                        task_name=task_name, beelog=self.blog,
                        yml_in_file=yml_in_file)
        out = adapt.allocate(test_only=test_only)

        if out is not None:
            self.blog.message("[" + str(task_name) + "] launched with job id: "
                              + str(out), color=self.blog.msg)

            # User input via yml
            yml_dict = None
            if yml_in_file is not None:
                yml_dict = (YMLLoader(yml_in_file, self.blog)).ymlfile

            # Database / logging
            ldb = LaunchDB(self._db_full, self.blog)
            ldb.new_launch(job_id=out, b_class=b_class, b_rjms=b_rjms,
                           status="Launched", beefile_full=beefile,
                           beefile_loc=file_loc, input_values=yml_dict)
        else:
            self.blog.message("Test launch complete!", task_name,
                              self.blog.msg)

    def terminate_task(self, job_id, rjms):
        adapt = Adapter(system=rjms, config=None, file_loc=None, task_name=None,
                        beelog=self.blog, yml_in_file=None)
        adapt.shutdown(job_id)


# Manage main argument responses
class BeeArguments(BeeLauncher):
    def __init__(self, beelog):
        BeeLauncher.__init__(self, beelog)

    def opt_launch(self, args):
        """
        Send launch request for single task to daemon
        :param args: command line argument namespace
        """
        filename = str(args.launch_task[0])
        f = BeefileLoader(filename, self.blog)

        yml_in = None
        if len(args.launch_task) > 1:
            yml_in = args.launch_task[1]

        self.launch(beefile=f.beefile, task_name=filename,
                    file_loc=path.dirname(path.abspath("{}.beefile".format
                                                       (filename))),
                    test_only=args.testonly, yml_in_file=yml_in)

    def opt_terminate(self, args):
        """
        Send termination request for specific task to daemon
        :param args: command line argument namespace
        """
        job_id = args.terminate_task[0]
        self.blog.message("Sending termination request.")
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

    def opt_examine(self, args):
        # TODO: document
        filename = str(args.examine_task[0])
        self.blog.message("Examining beefile", filename, )
        exam = BeefileExamine(filename, self.blog)
        # TODO: complete
        self.blog.message("Functionality not yet implemented!",
                          color=self.blog.err)
