class InputManagement(object):
    def __init__(self, beefile_input, user_values, beelog):
        self.bf_in = beefile_input
        self.usr_val = user_values
        self.blog = beelog
        self.variables = {}

    def update_in_var(self):
        for key in self.bf_in.keys():
            value = None
            try:
                value = self.usr_val.get(key,
                                         self.bf_in[key].get('default'))
            except KeyError:
                pass
            if value is None:
                self.blog.message("Unable to establish value for input variable: {}"
                                  .format(key), color=self.blog.err)
                exit(1)
            self.variables.update({key: value})

    def print_in_var(self):
        for key, value in self.variables.items():
            self.blog.message("\t{} = {}".format(key, value))
