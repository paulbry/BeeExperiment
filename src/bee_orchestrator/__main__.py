# system
import argparse
from termcolor import cprint
from os import path, remove, chdir
# project
from .bee_orc_ctl import ExecOrc
from bee_internal.beefile_manager import BeefileLoader
from bee_logging.bee_log import BeeLogging


# Parser supporting functions / classes
def verify_pyro4_conf():
    """
    Create json file used to share port set by Pryo4 across
    instance running orchestrator
    """
    conf_file = str(path.expanduser('~')) + "/.bee/port_conf.json"
    if path.isfile(conf_file):
        remove(conf_file)
    with open(conf_file, 'w') as file:
        file.write("{\"pyro4-ns-port\": 12345}")


parser = argparse.ArgumentParser(description="BEE Orchestrator\n"
                                             "https://github.com/lanl/BEE")


###############################################################################
# Bee Orchestrator
#
# orc: Launch standard BEE Orchestrator
# orc_arm: Launch ARM specific BEE Orchestrator
#
# task: Including this option allows for a bee specific task
#       (.beefile) that will automatically be launched to the orchestrator
###############################################################################
orc_group = parser.add_mutually_exclusive_group()
orc_group.add_argument("-o", "--orc",
                       action='store_true',
                       help="Launch Bee Orchestrator Controller")
orc_group.add_argument("-oa", "--orc_arm",
                       action='store_true',
                       help="Launch Bee Orchestrator Controller for ARM")

parser.add_argument("-t", "--task",
                    dest='task', nargs=1,
                    default=None,
                    help="Bee task (.beefile) you will to execute via orchestrator")
parser.add_argument("-i", "--input",
                    dest='input_file', nargs=1,
                    default=None,
                    help="<INPUT_FILE>.yml")

###############################################################################
# Un-organized arguments that can be
#
# There is no logging support from the bee-launcher, it is only designed
# to be implemented and utilised by the "orchestrator"
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


def manage_args(args):
    # check file requirements
    verify_pyro4_conf()

    beelog = BeeLogging(args.logflag, args.log_dest, args.quite)
    eo = ExecOrc(beelog)

    if args.task is not None:
        if args.orc:
            # TODO: support not full path?
            # bee-orchestrator -o -t $(pwd)/hello_lh
            p = args.task[0]
            t = p.rfind("/")
            chdir(p[:t])
            f = BeefileLoader(args.task[0], beelog)
            eo.main(f.beefile, p[t+1:len(p)])
        elif args.orc_arm:
            beelog.message("ARM support not ready at the moment!",
                           color=beelog.err)
        else:
            beelog.message("Please specify a valid orchestrator!",
                           color=beelog.err)

    elif args.orc:
        eo.main()
    elif args.orc_arm:
        beelog.message("ARM support not ready at the moment!",
                       color=beelog.err)


def main():
    try:
        args = parser.parse_args()
        # TODO: better method of dealing with empty namespace
        manage_args(args)
    except argparse.ArgumentError as e:
        cprint(e, "red")
        exit(1)


if __name__ == "__main__":
    main()
