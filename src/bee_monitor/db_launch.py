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
        cprint("Launcher DB - Query All", self._query_color)
        cursor = self.__connect_db()

        try:
            cursor.execute("SELECT * FROM launcher")
            print(cursor.fetchall())
        except sqlite3.OperationalError as e:
            cprint(str(e), self._error_color)

        self.__close_db()

    def __connect_db(self):
        self.__db_conn = sqlite3.connect(self._db_full)
        return self.__db_conn.cursor()

    def __close_db(self):
        self.__db_conn.close()
