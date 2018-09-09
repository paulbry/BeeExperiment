# system
import ast
import sqlite3


class LaunchDB(object):
    def __init__(self, db_location, beelog):
        self._db_full = db_location
        self.__db_conn = None
        self.blog = beelog

    def query_all(self):
        """
        Query launcher table for all entries and print in human-readable form
        SELECT * FROM launcher ORDER BY time ASC
        """
        cmd = "SELECT * FROM launcher ORDER BY time ASC"
        cursor = self.__connect_db()
        if self.execute_query(cursor, cmd):
            for line in cursor.fetchall():
                self.__print_all(line)
        self.__close_db()

    def delete_all(self):
        cmd = "DELETE FROM launcher"
        cursor = self.__connect_db()
        if self.execute_query(cursor, cmd):
            self.blog.message("All records deleted from launcher table",
                              color=self.blog.dbase)
        self.__close_db()

    def query_all_specific(self, index, value):
        """
        Query launcher table for all entries and print in human-readable forme
        SELECT * FROM launcher WHERE <index>=<value>
        """
        cmd = "SELECT * FROM launcher WHERE {}={}".format(
            str(index), str(value)
        )
        cursor = self.__connect_db()
        if self.execute_query(cursor, cmd):
            for line in cursor.fetchall():
                self.__print_all(line)
        self.__close_db()

    def query_value(self, index, value, result="*"):
        """
        Query launcher table for
        SELECT <result> FROM launcher WHERE <index>=<value>
        """
        cmd = "SELECT {} FROM launcher WHERE {}={}".format(
            str(result), str(index), str(value)
        )
        cursor = self.__connect_db()
        if self.execute_query(cursor, cmd):
            r = cursor.fetchone()[0]
        else:
            r = None
        self.__close_db()
        return r

    def execute_query(self, cursor, cmd):
        self.blog.message("Launcher DB - {}".format(cmd), color=self.blog.dbase)
        try:
            cursor.execute(cmd)
            return True
        except sqlite3.Error as e:
            self.blog.message("Error during: {}\n".format(cmd) + repr(e),
                              self._db_full, self.blog.err)
            return False
        except sqlite3.OperationalError as e:
            self.blog.message("Error during: {}\n".format(cmd) + repr(e),
                              self._db_full, self.blog.err)
            return False

    def _clean_dict(self, d, indent=1):
        for key, value in d.items():
            if isinstance(value, dict):
                self.blog.message('\t' * indent + str(key) + ":")
                self._clean_dict(value, indent + 1)
            else:
                self.blog.message('\t' * indent + str(key) + ": " + str(value))

    def __print_all(self, line):
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
        self.blog.message("Error: {}".format(line[11]),
                          color=self.blog.err)
        if line[13] is not None:
            self.blog.message("Input Values")
            self._clean_dict(ast.literal_eval(line[13]))

    def __connect_db(self):
        self.__db_conn = sqlite3.connect(self._db_full)
        return self.__db_conn.cursor()

    def __close_db(self, commit=True):
        if commit:
            self.__db_conn.commit()
        self.__db_conn.close()

    ###########################################################################
    # launcher table
    # TODO: document
    ###########################################################################
    def new_launch(self, job_id, b_class,
                   b_rjms=None, status=None, error=None,
                   beefile_name=None, beefile_full=None, beefile_loc=None,
                   beeflow_name=None, beeflow_loc=None, beeflow_full=None,
                   allocation_script=None, input_values=None):
        c = self.__connect_db()
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
        self.__close_db()

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
            self.__db_conn.commit()

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
                            beefile_full,
                            beeflow_name,
                            beeflow_loc,
                            beeflow_full,
                            error,
                            allocation_script,
                            input_values))
            self.__db_conn.commit()
        except sqlite3.Error as e:
            self.blog.message("Error during: insert_launch_event\n" + repr(e),
                              self._db_full, self.blog.err)
        except sqlite3.OperationalError as e:
            self.blog.message("Error during: insert_launch_event\n" + repr(e),
                              self._db_full, self.blog.err)
