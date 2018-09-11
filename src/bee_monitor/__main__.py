# system
import argparse
from os import path
from termcolor import cprint
# project
from .db_launch import LaunchDB
from bee_logging.bee_log import BeeLogging


# Database are currently hardcoded across the application
mon_homedir = path.expanduser('~')
mon_db_launch = mon_homedir + "/.bee/launcher.db"
mon_db_orchestrator = mon_homedir + "/.bee/orchestrator.db"


# Parser supporting functions
def verify_file(potential_file):
    if path.isfile(potential_file):
        return True
    else:
        cprint("[" + potential_file + "] Could not be found!", "red")
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
    ldb = None
    try:
        ldb = LaunchDB(BeeLogging(log=False, log_dest=None, quite=False))
    except Exception as e:
        cprint("Unable to load LaunchDB supporting class", "red")
        print(str(e))
        exit(1)

    # execute task if argument is present
    # exclusivity rules are managed by argparse groups
    if args.launch_all:
        ldb.query_all()
    elif args.delete_all:
        ldb.delete_all()

    if args.launch_custom:
        ldb.query_all_specific(args.launch_custom[0], args.launch_custom[1])
    elif args.launch_jobid:
        ldb.query_all_specific("jobid", str(args.launch_jobid[0]))
    elif args.launch_status:
        ldb.query_all_specific("status", str(args.launch_status[0]))


def orc_default(args):
    # TODO: implement & document
    cprint("Orchestrator monitoring not implemented!", "red")
    print(str(args))


parser = argparse.ArgumentParser(description="BEE Monitor\n"
                                             "https://github.com/paulbry/BeeExperiment")

###############################################################################
# Subparser based upon desired database / context
#
#   launcher -> bee-launcher
#   orchestrator -> bee-orchestrator
###############################################################################
subparser = parser.add_subparsers(title="Monitoring Targets")
sub_launch_group = subparser.add_parser("launcher",
                                        help="Details from bee-launcher")
sub_flow_group = subparser.add_parser("orchestrator",
                                      help="Details from bee-orchestrator")

###############################################################################
# Bee Launcher DB Related Monitoring
###############################################################################
launch_group = sub_launch_group.add_mutually_exclusive_group()
launch_group.add_argument("-a", "--all",
                          dest='launch_all', action='store_true',
                          help="Query launcher table for everything.")
launch_group.add_argument("-j", "--jobid",
                          dest='launch_jobid', nargs=1,
                          help="Query launcher table using jobid.")
launch_group.add_argument("-s", "--status",
                          dest='launch_status', nargs=1,
                          help="Query launcher table using job status.")
launch_group.add_argument("-c", "--custom",
                          dest='launch_custom', nargs=2,
                          help="Query launcher table using user-defined key/value.\n"
                               "... -c <index> <value>")
launch_group.add_argument("-da", "--delete-all",
                          dest='delete_all', action='store_true',
                          help="Completely clear launcher table.")
sub_launch_group.set_defaults(func=launch_default)

###############################################################################
# Bee Orchestrator DB Related Monitoring
###############################################################################
# TODO: add options for orchestrator


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
