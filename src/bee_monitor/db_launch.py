# system
import ast
import sqlite3
from os import path
# project
from .db_tools import SharedDBTools


class LaunchDB(SharedDBTools):
    def __init__(self, beelog):
        SharedDBTools.__init__(self, beelog, path.expanduser('~') + "/.bee/launcher.db")

    def query_all(self):
        """
        Query launcher table for all entries and print in human-readable form
        SELECT * FROM launcher ORDER BY time ASC
        """
        self._exec_query_all('launcher')

    def query_all_specific(self, index, value):
        """
        Query launcher table for all entries and print in human-readable forme
        SELECT * FROM launcher WHERE <index>=<value>
        """
        self._exec_query_all_specific('launcher', index, value)

    def query_value(self, index, value, result="*"):
        """
        Query launcher table for
        SELECT <result> FROM <db> WHERE <index> = <value>
        """
        r = self._exec_query_value('launcher', index, value, result)
        return r

    def delete_all(self):
        """
        Remove all entries from the specified table
        """
        self._exec_delete_all('launcher')

    def print_all(self, line):
        """
        Print data from launcher.db in readable format
        :param line: single line from SELECT * FROM launcher
        """
        self.blog.message("\nBeefile Name: {}".format(line[5]),
                          color=self.blog.dbase)
        self.blog.message("JobID: {}".format(line[1]))
        self.blog.message("Class: {}".format(line[2]))
        self.blog.message("Management System: {}".format(line[3]))
        self.blog.message("Status: {}".format(line[4]))
        self.blog.message("TimeStamp: {}".format(line[14]))
        self.blog.message("Beefile", color=self.blog.dbase)
        self._clean_dict(ast.literal_eval(line[7]))
        if line[8] is not None:
            self.blog.message("Beeflow Name: {}".format(line[8]))
            self.blog.message("Beeflow")
            self._clean_dict(ast.literal_eval(line[10]))
        if line[11] == "None":
            self.blog.message("Error: {}".format(line[11]),
                              color=self.blog.err)
        if line[13] != "None":
            self.blog.message("Input Values", color=self.blog.dbase)
            print(line[13])
            self._clean_dict(ast.literal_eval(line[13]))

    ###########################################################################
    # launcher table
    ###########################################################################
    def new_launch(self, job_id, b_class,
                   b_rjms=None, status=None, error=None,
                   beefile_name=None, beefile_full=None, beefile_loc=None,
                   beeflow_name=None, beeflow_loc=None, beeflow_full=None,
                   allocation_script=None, input_values=None):
        """
        Invoke when a new launch even occurs that needs to be tracked.
        The job_id (jobID), b_class (class), and b_rjms (manageSys) are
        required. Remaining parameters are optional.
        NOTE: creating the launcher table (if required) will be handled
        automatically.
        """
        c = self._connect_db()
        self.__launcher_table(c)
        self.__insert_launch_event(cursor=c, job_id=job_id, b_class=b_class,
                                   b_rjms=b_rjms, status=status, error=error,
                                   beefile_name=beefile_name,
                                   beefile_full=beefile_full,
                                   beefile_loc=beefile_loc,
                                   beeflow_name=beeflow_name,
                                   beeflow_loc=beeflow_loc,
                                   beeflow_full=beeflow_full,
                                   allocation_script=allocation_script,
                                   input_values=input_values)
        self._close_db()

    def __launcher_table(self, cursor):
        cmd = "CREATE TABLE IF NOT EXISTS launcher " \
              "(tableID INTEGER PRIMARY KEY, " \
              "jobID TEXT NOT NULL, " \
              "class TEXT NOT NULL, " \
              "manageSys TEXT, " \
              "status TEXT, " \
              "beefileName TEXT, " \
              "beefileLocation TEXT, " \
              "beefileFull TEXT, " \
              "beeflowName TEXT, " \
              "beeflowLocation TEXT, " \
              "beeflowFull TEXT, " \
              "errDetails TEXT, " \
              "allocationScript TEXT, " \
              "inputValues TEXT," \
              "time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL)"
        if self.execute_query(cursor, cmd):
            self._db_conn.commit()

    def __insert_launch_event(self, cursor, job_id, b_class, b_rjms=None,
                              status=None, error=None, beefile_name=None,
                              beefile_full=None, beefile_loc=None,
                              beeflow_name=None, beeflow_loc=None,
                              beeflow_full=None, allocation_script=None,
                              input_values=None):

        try:
            cursor.execute("INSERT INTO launcher ("
                           "jobID, "
                           "class, "
                           "manageSys, "
                           "status, "
                           "beefileName, "
                           "beefileLocation, "
                           "beefileFull, "
                           "beeflowName,"
                           "beeflowLocation, "
                           "beeflowFull, "
                           "errDetails, "
                           "allocationScript, "
                           "inputValues) "
                           "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (job_id,
                            b_class,
                            b_rjms,
                            status,
                            beefile_name,
                            beefile_loc,
                            str(beefile_full),
                            beeflow_name,
                            beeflow_loc,
                            str(beeflow_full),
                            str(error),
                            str(allocation_script),
                            str(input_values)))
            self._db_conn.commit()
        except sqlite3.Error as e:
            self.blog.message("Error during: insert_launch_event\n" + repr(e),
                              self._db_full, self.blog.err)
        except sqlite3.OperationalError as e:
            self.blog.message("Error during: insert_launch_event\n" + repr(e),
                              self._db_full, self.blog.err)
