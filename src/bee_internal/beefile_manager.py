# system
from yaml import load, YAMLError


class BeefileLoader(object):
    def __init__(self, file_name, beelog):
        try:
            stream = open("{}.beefile".format(file_name), "r")
            self.beefile = load(stream)
        except YAMLError as err:
            beelog.message(err, "{}.beefile".format(file_name), beelog.err)
            exit(1)


class BeeflowLoader(object):
    def __init__(self, flow_name, beelog):
        try:
            stream = open("{}.beeflow".format(flow_name), "r")
            self.beeflow = load(stream)
        except YAMLError as err:
            beelog.message(err, "{}.beeflow".format(flow_name), beelog.err)
            exit(1)
