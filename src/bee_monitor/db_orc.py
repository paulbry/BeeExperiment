# system
import sqlite3
from os import path
# project
from bee_monitor.db_tools import SharedDBTools


class OrchestratorDB(SharedDBTools):
    def __init__(self, beelog, monitored=True):
        SharedDBTools.__init__(self, beelog, "/var/tmp/orc.db", monitored)
        self.table = 'orchestrator'

    def query_all(self):
        """
        Query launcher table for all entries and print in human-readable form
        SELECT * FROM launcher ORDER BY time ASC
        """
        self._exec_query_all(self.table)

    def query_all_specific(self, index, value):
        """
        Query launcher table for all entries and print in human-readable forme
        SELECT * FROM launcher WHERE <index>=<value>
        """
        self._exec_query_all_specific(self.table, index, value)

    def query_value(self, index, value, result="*"):
        """
        Query launcher table for
        SELECT <result> FROM <db> WHERE <index> = <value>
        """
        r = self._exec_query_value(self.table, index, value, result)
        return r

    def print_all(self, line):
        """
        Print data from launcher.db in readable format
        :param line: single line from SELECT * FROM orchestrator
        """
        self.blog.message("\nCommand: {}".format(line[4]),
                          color=self.blog.dbase)
        self.blog.message("TaskID: {}".format(line[1]))
        if line[3] is not None:
            self.blog.message("JobID: {}".format(line[3]))
        self.blog.message("Status: {}".format(line[2]))
        if line[5] is not None:
            self.blog.message("stdOut: {}".format(line[5]))
        if line[6] is not None:
            self.blog.message("stdErr: {}".format(line[6]))
        if line[7] is not None and line[7] != 'None':
            self.blog.message("exitStatus: {}".format(line[7]))
        self.blog.message("event: {}".format(line[8]))
        self.blog.message("timeStamp: {}".format(line[9]))

    def delete_all(self):
        """
        Remove all entries from the specified table
        """
        self._exec_delete_all(self.table)

    ###########################################################################
    # orchestrator table
    ###########################################################################
    def new_orc(self, task_id, status,
                job_id=None, command=None,
                std_output=None, std_err=None, exit_status=None,
                event=None):
        if self.monitored:
            c = self._connect_db()
            self.__orc_table(c)
            self.__insert_orc_event(cursor=c, task_id=task_id, status=status,
                                    job_id=job_id, command=command, std_output=std_output,
                                    std_err=std_err, exit_status=exit_status,
                                    event=event)
            self._close_db()

    def __orc_table(self, cursor):
        cmd = "CREATE TABLE IF NOT EXISTS {} " \
              "(tableID INTEGER PRIMARY KEY, " \
              "taskID TEXT NOT NULL, " \
              "status INTEGER NOT NULL, " \
              "jobID TEXT, " \
              "command TEXT, " \
              "stdOutput TEXT, " \
              "stdErr TEXT, " \
              "exitStatus TEXT, " \
              "event TEXT, " \
              "time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT " \
              "NULL)".format(self.table)
        if self.execute_query(cursor, cmd):
            self._db_conn.commit()

    def __insert_orc_event(self, cursor, task_id, status,
                           job_id=None, command=None,
                           std_output=None, std_err=None, exit_status=None,
                           event=None):
        try:
            cursor.execute("INSERT INTO orchestrator ("
                           "taskID, "
                           "status, "
                           "jobID, "
                           "command, "
                           "stdOutput, "
                           "stdErr, "
                           "exitStatus,"
                           "event) "
                           "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (str(task_id),
                            status,
                            str(job_id),
                            str(command),
                            std_output,
                            std_err,
                            str(exit_status),
                            event))
            self._db_conn.commit()
        except sqlite3.Error as e:
            self.blog.message("Error during: insert_orc_event\n" + repr(e),
                              self._db_full, self.blog.err)
        except sqlite3.OperationalError as e:
            self.blog.message("Error during: insert_orc_event\n" + repr(e),
                              self._db_full, self.blog.err)
