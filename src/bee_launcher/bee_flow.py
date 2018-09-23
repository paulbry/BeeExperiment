# system
import os.path
import time
import calendar
from subprocess import Popen, CalledProcessError
# project
from bee_internal.beefile_manager import BeeflowLoader, BeefileLoader, \
    YMLLoader
from bee_logging.bee_log import BeeLogging
from .launcher_translator import Adapter
from bee_internal.in_out_manage import InputManagement
from bee_monitor.db_launch import LaunchDB


def terminate_flow_id(flow_id):
    pass


def terminate_flow_task(task_id):
    pass


class LaunchBeeFlow(object):
    def __init__(self, launch_flow, beelog):
        # objects
        self.blog = beelog
        self.ldb = LaunchDB(beelog=self.blog)
        self.bf_loader = BeeflowLoader(launch_flow, self.blog)

        self.flow_name = launch_flow
        self.beeflow = self.bf_loader.beeflow
        self.flow_id = "{}-{}".format(self.flow_name,
                                      calendar.timegm(time.gmtime()))
        self.j_id = 0
        # BEGIN
        self.launch_flow()

    def launch_flow(self):
        running_jobs = {}

        for file_name, val in self.beeflow.items():
            if not os.path.isfile(file_name + ".beefile"):
                self.blog.message("Unable to identify beefile named: "
                                  "{}".format(file_name),
                                  color=self.blog.err)
                terminate_flow_id(self.flow_id)
                exit(1)

            bf_loader = BeefileLoader(file_name, self.blog)
            beefile = bf_loader.beefile
            bf_file_loc = os.path.dirname(os.path.abspath("{}.beefile".
                                                          format(file_name)))
            depends = self.__build_depends(val, running_jobs)

            if val is not None:
                ocr = val.get('occurrences', 1)
                in_file = val.get('inputFile')
                in_gen = val.get('inputGenerator')
            else:
                ocr = 1
                in_file = None
                in_gen = None

            if ocr > 1:
                for x in range(0, ocr):
                    try:
                        beefile['id'] = file_name + "-{}".format(x)
                    except KeyError:
                        self.blog.message("Unable to identify {}.beefile id "
                                          "key".format(file_name),
                                          color=self.blog.err)
                        terminate_flow_id(self.flow_id)
                        exit(1)

                    jobid = self.__launch_task(beefile, beefile.get('id'), bf_file_loc,
                                               self.__manage_input(beefile, in_file,
                                                                   in_gen), depends)
                    existing = running_jobs.get(file_name)
                    if existing is not None:
                        running_jobs[file_name] += ",{}".format(jobid)
                    else:
                        running_jobs.update({file_name: str(jobid)})
            else:
                jobid = self.__launch_task(beefile, beefile.get('id'), bf_file_loc,
                                           self.__manage_input(beefile, in_file,
                                                               in_gen), depends)

                running_jobs.update({file_name: str(jobid)})

    ###########################################################################
    #
    ###########################################################################
    def __launch_task(self, beefile, task_name, file_loc, input_mng, depends):
        try:  # ResourceRequirements not required when using localhost
            b_rjms = beefile['requirements']['ResourceRequirement']['manageSys']
        except KeyError:
            b_rjms = "localhost"

        # TODO: offer support for more than SLURM
        if str(b_rjms).lower() != 'slurm':
            self.blog.message("Unable to support non slurm manageSys at this "
                              "time.", color=self.blog.err)
            terminate_flow_id(self.flow_id)
            exit(1)

        self.blog.message(msg="Preparing to launch..."
                              + "\n\tManageSys: {}".format(b_rjms)
                              + "\n\tTask: {}".format(task_name)
                              + "\n\tDependencies: {}".format(depends),
                          task_name=task_name,
                          color=self.blog.msg)

        adapt = Adapter(system=b_rjms, config=beefile, file_loc=file_loc,
                        task_name=task_name, beelog=self.blog,
                        input_mng=input_mng)
        # out = adapt.allocate()
        # TODO: remove TEMP!
        self.j_id += 1
        out = self.j_id

        if out is not None:
            self.blog.message(msg="Launched with job id: {}".format(out),
                              task_name=task_name, color=self.blog.msg)

            self.ldb.new_launch(job_id=out, b_rjms=b_rjms,
                                status="Launched", beefile_full=beefile,
                                beefile_loc=file_loc,
                                input_values=input_mng.variables,
                                beeflow_full=self.beeflow,
                                beeflow_id=self.flow_id,
                                beeflow_name=self.flow_name)
        else:
            self.blog.message(msg="Unexpected error during allocation",
                              task_name=task_name, color=self.blog.msg)
            terminate_flow_id(self.flow_id)
            exit(1)

        return out

    def __build_depends(self, val, running_jobs):
        depends = None
        if val is not None:
            if val.get("dependency_list") is not None:
                if val.get("dependency_mode") == "off-line":
                    for e in val.get("dependency_list"):
                        if depends is None:
                            depends = str(running_jobs.get(e))
                        else:
                            depends += ",{}".format(running_jobs.get(e))
                elif val.get("dependency_mode") == "in-situ":
                    # TODO: identify how to support?
                    pass
        return depends

    def __manage_input(self, beefile, in_file_name, gen_cmd):
        if gen_cmd is not None:
            self.__run_popen(gen_cmd)

        if in_file_name is not None:
            if not os.path.isfile(in_file_name):
                self.blog.message("Unable to identify input named: "
                                  "{}".format(in_file_name), self.blog.err)
                exit(1)
            y = YMLLoader(in_file_name, self.blog)
            return InputManagement(beefile, y.ymlfile, self.blog, in_file_name)
        else:
            return InputManagement(beefile, None, self.blog, None)

    def __run_popen(self, command):
        r_cmd = (''.join(str(x) + " " for x in command))
        self.blog.message("Executing inputGenerator: {}".format(r_cmd),
                          self.flow_name)
        try:
            p = Popen(command)
            p.wait()
        except CalledProcessError as e:
            self.blog.message(msg="Error during - " + str(r_cmd) + "\n" +
                                  str(e), color=self.blog.err)
            terminate_flow_id(self.flow_id)
            exit(1)
        except OSError as e:
            self.blog.message(msg="Error during - " + str(r_cmd) + "\n" +
                                  str(e), color=self.blog.err)
            terminate_flow_id(self.flow_id)
            exit(1)

