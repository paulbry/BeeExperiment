#!/usr/bin/python
# system
import os
import sqlite3
from termcolor import cprint
# project
from bee_internal.beefile_manager import BeefileLoader
from bee_monitor.db_launch import LaunchDB
from .launcher_translator import Adapter


class BeeLauncher(object):
    def __init__(self, log=False, log_dest="None"):
        # Logging configuration
        self._log = log  # log flag (T/F)
        self._log_dest = log_dest + ".launcher"  # log file destinations

        self.__homedir = os.path.expanduser('~')

        # Database Tracking
        # TODO: implemented options bee_conf file?
        self._db_full = self.__homedir + "/.bee/launcher.db"
        self.__db_conn = None

        # Termcolor messages
        self._error_color = 'red'
        self._message_color = 'cyan'
        self._warning_color = 'yellow'

    def launch(self, beefile, task_name, file_loc):
        b_class = self._fetch_beefile_value(dictionary=beefile, key="class",
                                            quit_err=True)
        b_rjms = self._fetch_beefile_value(dictionary=beefile['requirements']['ResourceRequirement'],
                                           key="manageSys", quit_err=True)
        cprint("[" + str(task_name) + "] Preparing to launch..." +
               "\n\tClass: " + str(b_class) + "\n\tRJMS: " + str(b_rjms),
               self._message_color)
        adapt = Adapter(system=b_rjms, config=beefile, file_loc=file_loc,
                        task_name=task_name)
        out = adapt.allocate()
        cprint("[" + str(task_name) + "] launched with job id: " + str(out),
               self._message_color)

        # Database / logging
        cursor = self.__connect_db()
        self.__launcher_table(cursor=cursor)
        self.__insert_launch_event(cursor=cursor, job_id=out, b_class=b_class,
                                   b_rjms=b_rjms, status="Launching",
                                   beefile_full=beefile,
                                   beefile_loc=file_loc)
        self.__close_db()

    def terminate_task(self, job_id, rjms):
        # TODO: utlize monitor to verify correct jobId?
        # TODO: idetnify way to communicate with ORC for clean shutdown?
        adapt = Adapter(system=rjms, config=None, file_loc=None, task_name=None)
        adapt.shutdown(job_id)

    def _fetch_beefile_value(self, dictionary, key, default=None,
                             quit_err=False, silent=False):
        try:
            return dictionary[key]
        except KeyError:
            if default is not None and not quit_err:
                if not silent:
                    cprint("User defined value for ["
                           + str(key) + "] was not found, default value: "
                           + str(default) + " used.", self._warning_color)
                return default
            else:
                cprint("Key: " + str(key) + " was not found",
                       self._error_color)
            exit(1)

    ###########################################################################
    # Database reflated functions
    # TODO: document
    ###########################################################################
    def __connect_db(self):
        self.__db_conn = sqlite3.connect(self._db_full)
        return self.__db_conn.cursor()

    def __close_db(self):
        self.__db_conn.close()

    def __launcher_table(self, cursor):
        try:
            cursor.execute("CREATE TABLE IF NOT EXISTS launcher "
                           "(tableID INTEGER PRIMARY KEY, "
                           "jobID TEXT NOT NULL, "
                           "class TEXT NOT NULL, "
                           "manageSys TEXT, "
                           "status TEXT, "
                           "beefileName TEXT, "
                           "beefileLocation TEXT,"
                           "beefileFull TEXT, "
                           "beeflowName TEXT, "
                           "beeflowLocation TEXT,"
                           "beeflowFull TEXT, "
                           "errDetails TEXT, "
                           "allocationScript TEXT,"
                           "time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL)")
            self.__db_conn.commit()
        except sqlite3.Error as e:
            cprint("[" + self._db_full + "]Error while creating launcher table",
                   self._error_color)
            print(e)

    def __insert_launch_event(self, cursor, job_id, b_class, b_rjms=None,
                              status=None, error=None, beefile_name=None,
                              beefile_full=None, beefile_loc=None,
                              beeflow_name=None, beeflow_loc=None,
                              beeflow_full=None):
        cursor.execute("INSERT INTO launcher "
                       "(jobID, class, manageSys, status, beefileName, "
                       "beefileLocation, beefileFull, beeflowName,"
                       "beeflowLocation, beeflowFull, errDetails) "
                       "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (job_id, b_class, b_rjms, status, beefile_name,
                        beefile_loc, str(beefile_full), beeflow_name,
                        beeflow_loc, str(beeflow_full), str(error)))
        self.__db_conn.commit()


# Manage main argument responses
class BeeArguments(BeeLauncher):
    def __init__(self, log=False, log_dest='/var/tmp/bee.log'):
        BeeLauncher.__init__(self, log, log_dest)

    def opt_launch(self, args):
        """
        Send launch request for single task to daemon
        :param args: command line argument namespace
        """
        beefile = str(args.launch_task[0])
        f = BeefileLoader(beefile)
        self.launch(beefile=f.beefile, task_name=beefile,
                    file_loc=os.path.dirname(os.path.abspath("{}.beefile".format
                                                             (beefile))))

    def opt_terminate(self, args):
        """
        Send termination request for specific task to daemon
        :param args: command line argument namespace
        """
        job_id = args.terminate_task[0]
        print("Sending termination request.")
        db = LaunchDB(self._db_full)
        rjms = db.query_value("jobID", job_id, "manageSys")
        if rjms is not None:
            self.terminate_task(job_id, rjms)
        else:
            cprint("No task identified with JobID: {}".format(job_id),
                   'red')
        cprint("Task: " + job_id + " is terminated.", 'cyan')

    # TODO: implement high level status support using job id
    def opt_status(self):
        pass
