# system
import os
from threading import Thread, Event
from termcolor import cprint
from pwd import getpwuid


class BeeTask(Thread):
    def __init__(self, task_id, beefile):
        Thread.__init__(self)

        # Task configuration
        self.platform = None
        self._beefile = beefile
        self._task_id = task_id
        self._task_label = self._beefile.get('label', 'BEE: {}'.
                                             format(self._task_id))

        # System configuration
        self._user_name = getpwuid(os.getuid())[0]

        # Output colors
        self._output_color = "cyan"
        self._error_color = "red"
        self._warning_color = "yellow"

        # Events for workflow
        self.__begin_event = None
        self.__end_event = None
        self.__event_list = []

    # Event/Trigger management
    @property
    def begin_event(self):
        return self.__begin_event

    @begin_event.setter
    def begin_event(self, flag):
        # TODO: document
        if flag == 0:
            self.__begin_event = Event()
        elif flag == 1:
            self.__begin_event.set()
        else:
            self.__begin_event.clear()

    @property
    def end_event(self):
        return self.__end_event

    @end_event.setter
    def end_event(self, flag):
        # TODO: document
        if flag == 0:
            self.__end_event = Event()
        elif flag == 1:
            self.__end_event.set()
        else:
            self.__end_event.clear()

    @property
    def event_list(self):
        return self.__event_list

    @event_list.setter
    def event_list(self, new_event):
        """
        Append event to event_list
        :param new_event:
        """
        self.__event_list.append(new_event)

    # Standard BEE methods
    def run(self):
        pass

    def launch(self):
        pass

    def execute_workers(self):
        pass

    def execute_base(self):
        pass

    def terminate(self):
        pass

    # Task management support functions (private)
    def _handle_message(self, msg, color=None):
        """
        :param msg: To be printed to console
        :param color: If message is be colored via termcolor
                        Default = none (normal print)
        """

        if color is None:
            print("[{}] {}".format(self._task_id, msg))
        else:
            cprint("[{}] {}".format(self._task_id, msg), color)

    def _fetch_beefile_value(self, key, dictionary, default=None, quit_err=False,
                              silent=False):
        """
        Fetch a specific key/value pair from the .beefile and
        raise error is no default supplied and nothing found
        :param key: Key for value in dictionary
        :param dictionary: dictionary to be searched
                            e.g. self.__beefile['task_conf']
        :param default: Returned if no value found, if None (def)
                        then error message surfaced
        :param quit_err: Exit with non-zero (default=False)
        :param silent: Hide warning message (default=False)
        :return: Value for key. Data type dependent on beefile,
                    and no verification beyond existence
        """
        try:
            return dictionary[key]
        except KeyError:
            if default is not None and not quit_err:
                if not silent:
                    cprint("[" + self._task_id + "] User defined value for ["
                           + str(key) + "] was not found, default value: "
                           + str(default) + " used.", self._warning_color)
                return default
            else:
                cprint("[" + self._task_id + "] Key: " + str(key) + " was not found in: " +
                       str(dictionary), self._error_color)
                exit(1)
