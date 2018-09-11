class InputManagement(object):
    def __init__(self, beefile_input, user_values, beelog, yml_file_name):
        self.bf_in = beefile_input.get('inputs')
        self.yml_file_name = yml_file_name
        self.usr_val = user_values
        self.blog = beelog
        self.variables = None
        self.__pre = "${"
        self.__post = "}$"

        if self.bf_in is not None and self.usr_val is not None:
            self.variables = {}
            self.generate_in_var()

    def prepare_base_cmd(self, base_cmd):
        if base_cmd is not None:
            cmd = [base_cmd]
            return cmd
        return None

    def generate_in_var(self):
        for key in self.bf_in.keys():
            value = None
            try:
                value = self.usr_val.get(key,
                                         self.bf_in[key].get('default'))
            except KeyError:
                pass
            if value is None:
                value = self.bf_in[key].get('default')
                if value is None:
                    self.blog.message("Unable to establish value for input "
                                      "variable: {}".format(key),
                                      color=self.blog.err)
                exit(1)
            self.variables.update({key: value})

    def print_in_var(self):
        for key, value in self.variables.items():
            self.blog.message("\t{} = {}".format(key, value))

    def check_str(self, tar):
        loc = 0
        while loc != -1:
            loc = tar.find(self.__pre, loc)
            if loc != -1:
                x = tar.find(self.__post, loc)
                if x == -1:
                    self.blog.message("Error checking: {}\nVerify input variable "
                                      "syntax.", color=self.blog.err)
                    exit(1)
                tmp = self.variables.get(tar[loc+2:x])
                if tmp is not None:
                    tar = tar.replace(tar[loc:x] + self.__post, tmp)
                else:
                    self.blog.message("Error checking: {}\nNo matching input "
                                      "found.", color=self.blog.err)
                loc = x
        return tar
