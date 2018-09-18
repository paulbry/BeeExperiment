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
            if self.bf_in is not None:
                binds = []
                for key in self.bf_in:
                    binding = self.bf_in[key].get('inputBinding')
                    if binding is not None:
                        try:
                            binds.append([binding['position'], key, binding.get('prefix'),
                                          self.bf_in[key]['type']])
                        except KeyError:
                            self.blog.message("Unable to identify [position] for input "
                                              "key {}.".format(key), color=self.blog.err)
                            exit(1)
                if binds:
                    binds.sort()
                    for b in binds:
                        if b[2] is not None:
                            cmd.append(b[2])
                        x = self.variables.get(b[1])
                        if x is None:
                            self.blog.message("Variable {} has not been provided a "
                                              "value.\n Please verify you inputs "
                                              "and any defined outputs!",
                                              color=self.blog.err)
                        else:
                            t = b[3].lower()
                            if t == "boolean":
                                pass
                            elif t == "int":
                                cmd.append(str(x))
                            elif t == "string":
                                # cmd.append("\'{}\'".format(x))
                                cmd.append(x)
                            elif t == "file":
                                cmd.append(x)
                            else:
                                self.blog.message("Unsupported input type {}"
                                                  " detected".format(t),
                                                  color=self.blog.err)
            return cmd
        return None

    def update_vars(self, key, value):
        x = self.variables.get(key)
        if x is not None:
            ex_type = type(x)
            if ex_type == type(value):
                self.variables.update({key: value})
            else:
                if x == int:
                    self.variables.update({key: int(value)})
                elif x == str:
                    self.variables.update({key: str(value)})
                elif x == bool:
                    self.variables.update({key: bool(value)})
                else:
                    self.blog("Unsupported type {} detected during update_vars()"
                              "\nPlease contact to the developer for "
                              "support!".format(type(value)), color=self.blog.err)
                    exit(1)
        else:
            self.variables.update({key: value})
        print(self.variables)

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
        print(str(tar))
        print(type(tar))
        if isinstance(tar, str):
            loc = 0
            star = str(tar)
            try:
                while loc != -1:
                    loc = star.find(self.__pre, loc)
                    if loc != -1:
                        x = star.find(self.__post, loc)
                        if x == -1:
                            self.blog.message("Error checking: {}\nVerify input variable "
                                              "syntax.", color=self.blog.err)
                            exit(1)
                        tmp = self.variables.get(star[loc+2:x])
                        if tmp is not None:
                            star = star.replace(star[loc:x] + self.__post, tmp)
                        else:
                            self.blog.message("Error checking: {}\nNo matching input "
                                              "found.", color=self.blog.err)
                            exit(1)
                        loc = x
                return star
            except AttributeError as e:
                self.blog.message("Error checking user supplied variables/inputs. Insure "
                                  "that all expected values have been supplied:\n"
                                  "{}\n{}".format(self.variables, e), color=self.blog.err)
                exit(1)
        else:  # unsupported type (still return string for cmd list
            return str(tar)
