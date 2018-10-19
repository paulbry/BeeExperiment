# 3rd party
from yaml import safe_load, YAMLError


class BeefileLoader(object):
    def __init__(self, file_name, beelog):
        try:
            stream = open("{}.beefile".format(file_name), "r")
            self.beefile = safe_load(stream)
            stream.close()
        except YAMLError as err:
            beelog.message(err, "{}.beefile".format(file_name), beelog.err)
            exit(1)
        except FileNotFoundError as err:
            beelog.message(err, file_name, beelog.err)
            exit(1)


class BeefileExamine(BeefileLoader):
    def __init__(self, file_name, beelog):
        BeefileLoader.__init__(self, file_name, beelog)
    # TODO: identify method for verifying


class BeeflowLoader(object):
    def __init__(self, flow_name, beelog):
        try:
            stream = open("{}.beeflow".format(flow_name), "r")
            self.beeflow = safe_load(stream)
        except YAMLError as err:
            beelog.message(err, "{}.beeflow".format(flow_name), beelog.err)
            exit(1)
        except FileNotFoundError as err:
            beelog.message(err, flow_name, beelog.err)
            exit(1)


class BeeflowExamine(BeeflowLoader):
    def __init__(self, file_name, beelog):
        BeeflowLoader.__init__(self, file_name, beelog)
    # TODO: identify method for verifying


class YMLLoader(object):
    def __init__(self, file_name, beelog):
        try:
            stream = open(file_name, "r")
            self.ymlfile = safe_load(stream)
        except YAMLError as err:
            beelog.message(err, file_name, beelog.err)
            exit(1)
