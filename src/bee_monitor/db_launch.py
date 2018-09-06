# system
import ast
import sqlite3
from termcolor import cprint


class LaunchDB(object):
    def __init__(self, db_location):
        self._db_full = db_location
        self.__db_conn = None

        # Termcolor
        self._warning_color = "yellow"
        self._error_color = "red"
        self._query_color = "green"

    def query_all(self):
        """
        Query launcher table for all entries and print in human-readable form
        SELECT * FROM launcher
        """
        cmd = "SELECT * FROM launcher"
        cursor = self.__connect_db()
        if self.execute_query(cursor, cmd):
            for line in cursor.fetchall():
                self.__print_all(line)
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
        SELECT <result> FOMR launcher WHERE <index>=<value>
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
        cprint("Launcher DB - {}".format(cmd), self._query_color)
        try:
            cursor.execute(cmd)
            return True
        except sqlite3.OperationalError as e:
            cprint(str(e), self._error_color)
            return False

    def _clean_dict(self, d, indent=1):
        for key, value in d.items():
            if isinstance(value, dict):
                print('\t' * indent + str(key) + ":")
                self._clean_dict(value, indent + 1)
            else:
                print('\t' * indent + str(key) + ": " + str(value))

    def __print_all(self, line):
        """
        Print data from launcher.db in readable format
        :param line: single line from SELECT * FROM launcher
        """
        cprint("\nBeefile Name: {}".format(line[5]), self._query_color)
        print("JobID: {}".format(line[1]))
        print("Class: {}".format(line[2]))
        print("Management System: {}".format(line[3]))
        print("Status: {}".format(line[4]))
        print("TimeStamp: {}".format(line[13]))
        cprint("Beefile", self._query_color)
        self._clean_dict(ast.literal_eval(line[7]))
        if line[8] is not None:
            print("Beeflow Name: {}".format(line[8]))
            print("Beeflow")
            self._clean_dict(ast.literal_eval(line[10]))
        cprint("Error: {}".format(line[11]), "red")

    def __connect_db(self):
        self.__db_conn = sqlite3.connect(self._db_full)
        return self.__db_conn.cursor()

    def __close_db(self):
        self.__db_conn.close()
