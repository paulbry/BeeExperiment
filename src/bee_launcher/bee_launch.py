# system
from os import path
# project
from bee_internal.beefile_manager import BeefileLoader, BeefileExamine, \
    YMLLoader
from bee_internal.in_out_manage import InputManagement
from bee_launcher.launcher_translator import Adapter
from bee_monitor.db_launch import LaunchDB


class BeeLauncher(object):
    def __init__(self, beelog):
        self.blog = beelog  # Logging configuration object

    def launch(self, beefile, task_name, file_loc,
               test_only=False, input_mng=None):
        """
        Establish allocation via user defined requirements and invoke
        management system (e.g. slurm) to allocation and initiate orchestrator
        :param beefile: BeefileLoader.beefile
        :param task_name: Name of beefile as provided via command
        :param file_loc: Full path to beefile
        :param test_only: boolean
        :param input_mng: User provided input yml file (filename.yml)
                                Not opened during launch step, used during
                                orchestration
        """
        try:  # ResourceRequirements not required when using localhost
            b_rjms = beefile['requirements']['ResourceRequirement']['manageSys']
        except KeyError:
            b_rjms = "localhost"

        self.blog.message(msg="Preparing to launch..."
                              + "\n\tManageSys: {}".format(b_rjms)
                              + "\n\tTask: {}".format(task_name),
                          task_name=task_name,
                          color=self.blog.msg)

        adapt = Adapter(system=b_rjms, config=beefile, file_loc=file_loc,
                        task_name=task_name, beelog=self.blog,
                        input_mng=input_mng)
        out = adapt.allocate(test_only=test_only)

        if out is not None:
            self.blog.message(msg="Launched with job id: {}".format(out),
                              task_name=task_name, color=self.blog.msg)

            ldb = LaunchDB(beelog=self.blog)
            ldb.new_launch(job_id=out, b_rjms=b_rjms,
                           status="Launched", beefile_full=beefile,
                           beefile_loc=file_loc, input_values=input_mng.variables)
        elif test_only:
            self.blog.message(msg="Test launch complete!",
                              task_name=task_name, color=self.blog.msg)
        else:
            self.blog.message(msg="Unexpected error during allocation",
                              task_name=task_name, color=self.blog.msg)
        return out

    def terminate_task(self, job_id, rjms):
        adapt = Adapter(system=rjms, config=None, file_loc=None, task_name=None,
                        beelog=self.blog, input_mng=None)
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
        bff = {}
        try:
            bff = BeefileLoader(filename, self.blog)
        except FileNotFoundError as err:
            self.blog("Please verify name/existence of: {}\n{}".format(filename, err),
                      color=self.blog.err)
            exit(1)

        if len(args.launch_task) == 2 and args.launch_task[1] is not None:
            y = YMLLoader(args.launch_task[1], self.blog)
            input_mng = InputManagement(bff.beefile, y.ymlfile,
                                        self.blog, args.launch_task[1])
        else:
            input_mng = InputManagement(bff.beefile, None, self.blog, None)

        self.launch(beefile=bff.beefile, task_name=filename,
                    file_loc=path.dirname(path.abspath("{}.beefile".format
                                                       (filename))),
                    test_only=args.testonly, input_mng=input_mng)

    def opt_terminate(self, args):
        """
        Send termination request for specific task to daemon
        :param args: command line argument namespace
        """
        job_id = args.terminate_task[0]
        self.blog.message("Sending termination request.")
        db = LaunchDB(beelog=self.blog)
        rjms = db.query_value("jobID", job_id, "manageSys")
        if rjms is not None:
            self.terminate_task(job_id, rjms)
        else:
            self.blog.message("No task identified with JobID: {}".format(job_id),
                              color=self.blog.err)
        self.blog.message("Task: " + job_id + " is terminated.",
                          color=self.blog.msg)

    def opt_examine(self, args):
        """
        Examine user supplied beefile/input values to verify structure is
        correct. Content is not checked on YAML and key spelling!
        :param args: command line argument namespace
        """
        filename = str(args.examine_task[0])
        self.blog.message("Examining beefile", filename, )
        exam = BeefileExamine(filename, self.blog)
        # TODO: complete
        self.blog.message("Functionality not yet implemented!",
                          color=self.blog.err)
