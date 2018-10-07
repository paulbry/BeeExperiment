# 3rd party
import yaml


def main():
    try:
        source = 'input.yml'
        target = 'worker_input.yml'

        stream = open(source, "r")
        ymlfile = yaml.safe_load(stream)

        num = ymlfile.get('worker_num')

        print(num)
        num += 1

        if num < ymlfile.get('flow_occurences'):
            ymlfile['worker_num'] = num
        else:
            ymlfile['worker_num'] = 0

        stream.close()

        with open(target, "w") as w:
            dump = yaml.dump({'workerNum': num}, default_flow_style=False)
            w.write(dump)

        with open(source, "w") as x:
            dump = yaml.dump(ymlfile, default_flow_style=False)
            x.write(dump)

    except yaml.YAMLError as err:
        print(err)
        exit(1)


if __name__ == "__main__":
    main()
