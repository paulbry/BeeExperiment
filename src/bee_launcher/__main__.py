# system
import argparse
from os import getcwd, path
from termcolor import cprint
# project
from .bee_launch import BeeArguments
from bee_logging.bee_log import BeeLogging


# Parser supporting functions
def verify_launch_file(potential_file):
    """
    Checks if file specified exists, if not errors and
    halts application
    :param potential_file: argument provided by user (name)
    :return: argument IF .beefile found
    """
    ext = potential_file[-4:]
    if ext == "yaml" or ext == ".yml":
        tar = getcwd() + '/' + potential_file
    else:  # assume beefile
        if potential_file[-8:] == ".beefile":
            potential_file = potential_file[:-8]
        tar = getcwd() + '/' + potential_file + '.beefile'
    if path.isfile(tar):
        return potential_file
    else:
        cprint(potential_file + "{} cannot be found".format(tar), "red")
        exit(1)


def verify_single_beeflow(potential_file):
    """
    Checks if file specified exists, if not errors and
    halts application
    :param potential_file: argument provided by user (name)
    :return: argument IF .beeflow found
    """
    tar = getcwd() + "/" + potential_file + '.beeflow'
    if path.isfile(tar):
        return potential_file
    else:
        cprint(potential_file + "{} cannot be found".format(tar), "red")
        exit(1)


###############################################################################
# Default arg functions, responsible for identifying and acting upon arguments
# from specified sub-parsers
# package --arg subparser --subarg task_name
# Example: bee --logflag launch -l
#
# See Python official documentation:
# https://docs.python.org/2.7/library/argparse.html
###############################################################################
def launch_default(args):
    bee_args = None
    bl = BeeLogging(args.logflag, args.log_dest, args.quite)
    try:
        bee_args = BeeArguments(bl)
    except Exception as err:
        bl.message("Error during launch\n{}".format(err), color=bl.err)
        exit(1)

    # execute task if argument is present
    # exclusivity rules are managed by argparse groups
    if args.launch_task:
        bee_args.opt_launch(args)

    if args.terminate_task:
        bee_args.opt_terminate(args)

    if args.examine_task:
        bee_args.opt_examine(args)


def flow_default(args):
    # TODO: update upon implementation
    # BeeFlow(args.logflag, args.log_dest).main(args.launch_flow[0])
    bl = BeeLogging(args.logflag, args.log_dest, args.quite)
    bl.message("Not yet implemented!", bl.err)


parser = argparse.ArgumentParser(description="BEE Launcher\n"
                                             "https://github.com/paulbry/BeeExperiment")

###############################################################################
# Un-organized arguments that can be used to augment the launch process
###############################################################################
parser.add_argument("--logflag",
                    action="store_true", dest="logflag",
                    default=False,
                    help="Flag logger (default=False)")
parser.add_argument("--logfile",
                    dest='log_dest', nargs=1,
                    default="/var/tmp/bee.log",
                    help="Target destination for log file (default=/var/tmp/bee.log)")
parser.add_argument("-q", "--quite",
                    dest='quite', action="store_true",
                    default=False,
                    help="Suppress non-error console messages. Will "
                         "override any logging requests.")
parser.add_argument("--test-only",
                    action="store_true", dest="testonly",
                    default=False,
                    help="Validate and create launcher script but avoid executing it.")

###############################################################################
# Bee Launcher
# Launching/removing a task is currently only supported individually, thus
# they should remain mutually exclusive (launch_group)
#
# Bee Flow (composer)
###############################################################################
launch_group = parser.add_mutually_exclusive_group()
launch_group.add_argument("-l", "--launch",
                          dest='launch_task', nargs='*',
                          type=verify_launch_file,
                          help="Runs task specified by <LAUNCH_TASK>.beefile, "
                               "that needs to be in the current directory\n"
                               "If <INPUT_FILE>.yaml required also include")
launch_group.add_argument("-t", "--terminate",
                          dest='terminate_task', nargs=1,
                          help="Terminate tasks <TERMINATE_TASK> by "
                               "shutting/canceling any associated allocations "
                               "by jobID.")
launch_group.add_argument("-f", "--beeflow",
                          dest='launch_flow', nargs=1,
                          type=verify_single_beeflow,
                          help="Runs task specified by <LAUNCH_FLOW>.beeflow, "
                               "that needs to be in the current directory")
launch_group.add_argument("-e", "--examine",
                          dest='examine_task', nargs=1,
                          help="Examine supplied Beefile for structure & key "
                               "validity.")
launch_group.set_defaults(func=launch_default)


def main():
    try:
        args = parser.parse_args()
        # TODO: better method of dealing with empty namespace
        args.func(args)
    except argparse.ArgumentError as e:
        cprint(e, "red")
        exit(1)


if __name__ == "__main__":
    main()
