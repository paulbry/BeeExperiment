# system
import argparse
from os import path
from termcolor import cprint
# project
from .db_launch import LaunchDB
from bee_logging.bee_log import BeeLogging


# Variable required in script
# TODO: clean up and implement optional bee_conf
mon_homedir = path.expanduser('~')
mon_db_launch = mon_homedir + "/.bee/launcher.db"


# Parser supporting functions
def verify_file(potential_file):
    # TODO: document
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
        ldb = LaunchDB(mon_db_launch, BeeLogging(log=False, log_dest=None,
                                                 quite=False))
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

    if args.launch_jobid:
        print("launch jobid")

    if args.launch_status:
        print("launch status!")


def orc_default(args):
    # TODO: implement & document
    cprint("Orchestrator monitoring not implemented!", "red")
    print(str(args))


parser = argparse.ArgumentParser(description="BEE Monitor\n"
                                             "https://github.com/paulbry/BeeExperiment")

###############################################################################
# TODO: document
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
launch_group.add_argument("-da", "--delete-all",
                          dest='delete_all', action='store_true',
                          help="Completely clear launcher table.")
# TODO: document status (in BEE terms)

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
