# system
import sqlite3


class SharedDBTools(object):
    def __init__(self, beelog, db_full):
        self.blog = beelog

        # Database Tracking (atm hardcoded location!)
        self._db_full = db_full
        self._db_conn = None


    # PUBLIC
    def execute_query(self, cursor, cmd):
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

    def _exec_delete_all(self, table_name):
        """
        Remove all entries from the specified table
        """
        cmd = "DELETE FROM {}".format(table_name)
        cursor = self._connect_db()
        if self.execute_query(cursor, cmd):
            self.blog.message("All records deleted from launcher table",
                              color=self.blog.dbase)
        self._close_db()

    def print_all(self, line):
        # Needs to be defined for each database
        pass

    # PROTECTED
    def _connect_db(self):
        self._db_conn = sqlite3.connect(self._db_full)
        return self._db_conn.cursor()

    def _close_db(self, commit=True):
        if commit:
            self._db_conn.commit()
        self._db_conn.close()

    def _clean_dict(self, d, indent=1):
        """
        Print (to console) the Python dicationary passed (d).
        """
        for key, value in d.items():
            if isinstance(value, dict):
                self.blog.message('\t' * indent + str(key) + ":")
                self._clean_dict(value, indent + 1)
            else:
                self.blog.message('\t' * indent + str(key) + ": " + str(value))

    def _exec_query_value(self, table, index, value, result="*"):
        cmd = "SELECT {} FROM {} WHERE {}={}".format(
            result, table, index, str(value)
        )
        cursor = self._connect_db()
        if self.execute_query(cursor, cmd):
            r = cursor.fetchone()[0]
        else:
            r = None
        self._close_db()
        return r

    def _exec_query_all(self, table):
        cmd = "SELECT * FROM {} ORDER BY time ASC".format(table)
        cursor = self._connect_db()
        if self.execute_query(cursor, cmd):
            for line in cursor.fetchall():
                self.print_all(line)
        self._close_db()

    def _exec_query_all_specific(self, table, index, value):
        cmd = "SELECT * FROM {} WHERE {}='{}'".format(
            table, index, value
        )
        cursor = self._connect_db()
        if self.execute_query(cursor, cmd):
            for line in cursor.fetchall():
                self.print_all(line)
        self._close_db()
