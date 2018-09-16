# system
import sqlite3
from os import path
# project
from .db_tools import SharedDBTools


class OrchestratorDB(SharedDBTools):
    def __init__(self, beelog):
        SharedDBTools.__init__(self, beelog, path.expanduser('~') + "/.bee/orc.db")

    def query_all(self):
        """
        Query launcher table for all entries and print in human-readable form
        SELECT * FROM launcher ORDER BY time ASC
        """
        self._exec_query_all('orchestrator')

    def query_all_specific(self, index, value):
        """
        Query launcher table for all entries and print in human-readable forme
        SELECT * FROM launcher WHERE <index>=<value>
        """
        self._exec_query_all_specific('orchestrator', index, value)

    def query_value(self, index, value, result="*"):
        """
        Query launcher table for
        SELECT <result> FROM <db> WHERE <index> = <value>
        """
        r = self._exec_query_value('orchestrator', index, value, result)
        return r

    def print_all(self, line):
        """
        Print data from launcher.db in readable format
        :param line: single line from SELECT * FROM orchestrator
        """
        self.blog.message("\nCommand: {}".format(line[4]),
                          color=self.blog.dbase)
        self.blog.message("TaskID: {}".format(line[1]))
        self.blog.message("JobID: {}".format(line[3]))
        self.blog.message("Status: {}".format(line[2]))
        self.blog.message("stdOut: {}".format(line[5]))
        self.blog.message("stdErr: {}".format(line[6]))
        self.blog.message("exitStatus: {}".format(line[7]))
        self.blog.message("timeStamp: {}".format(line[8]))

    def delete_all(self):
        """
        Remove all entries from the specified table
        """
        self._exec_delete_all('orchestrator')

    ###########################################################################
    # orchestrator table
    ###########################################################################
    def new_orc(self, task_id, status,
                job_id=None, command=None,
                std_output=None, std_err=None, exit_status=None):
        c = self._connect_db()
        self.__orc_table(c)
        self.__insert_orc_event(cursor=c, task_id=task_id, status=status,
                                job_id=job_id, command=command, std_output=std_output,
                                std_err=std_err, exit_status=exit_status)
        self._close_db()

    def __orc_table(self, cursor):
        cmd = "CREATE TABLE IF NOT EXISTS orchestrator " \
              "(tableID INTEGER PRIMARY KEY, " \
              "taskID TEXT NOT NULL, " \
              "status TEXT NOT NULL, " \
              "jobID TEXT, " \
              "command TEXT, " \
              "stdOutput TEXT, " \
              "stdErr TEXT, " \
              "exitStatus TEXT, " \
              "time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL)"
        if self.execute_query(cursor, cmd):
            self._db_conn.commit()

    def __insert_orc_event(self, cursor, task_id, status,
                           job_id=None, command=None,
                           std_output=None, std_err=None, exit_status=None):

        try:
            cursor.execute("INSERT INTO launcher ("
                           "taskID, "
                           "status, "
                           "jobID, "
                           "command, "
                           "stdOutput, "
                           "stdErr, "
                           "exitStatus) "
                           "VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (task_id,
                            status,
                            job_id,
                            command,
                            std_output,
                            std_err,
                            str(exit_status)))
            self._db_conn.commit()
        except sqlite3.Error as e:
            self.blog.message("Error during: insert_launch_event\n" + repr(e),
                              self._db_full, self.blog.err)
        except sqlite3.OperationalError as e:
            self.blog.message("Error during: insert_launch_event\n" + repr(e),
                              self._db_full, self.blog.err)
