# system
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
        # TODO: document
        # TODO: expand display
        cmd = "SELECT * FROM launcher"
        cprint("Launcher DB - {}".format(cmd), self._query_color)
        cursor = self.__connect_db()

        try:
            cursor.execute(cmd)
            print(cursor.fetchall())
        except sqlite3.OperationalError as e:
            cprint(str(e), self._error_color)

        self.__close_db()

    def query_value(self, index, value, result="*"):
        cmd = "SELECT {} FROM launcher WHERE {}={}".format(
            str(result), str(index), str(value)
        )
        cprint("Launcher DB - {}".format(cmd), self._query_color)
        cursor = self.__connect_db()

        r = None
        try:
            cursor.execute(cmd)
            r = cursor.fetchone()
        except sqlite3.OperationalError as e:
            cprint(str(e), self._error_color)

        self.__close_db()
        return r

    def __connect_db(self):
        self.__db_conn = sqlite3.connect(self._db_full)
        return self.__db_conn.cursor()

    def __close_db(self):
        self.__db_conn.close()
