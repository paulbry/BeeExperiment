# system
from getpass import getuser
from tempfile import NamedTemporaryFile
# 3rd party
import boto3
# project
from bee_internal.shared_tools import TranslatorMethods


class AWSAdaptee:
    def __init__(self, config, file_loc, task_name, beelog, input_mng,
                 remote=None):
        # constants
        self._encode = 'UTF-8'

        # task /configuration
        self._beefile = config
        if self._beefile is not None:
            self._beefile_req = self._beefile.get('requirements')
        else:
            self._beefile_req = {}
        self._file_loc = file_loc
        self._task_name = task_name
        self.__user = getuser()

        # daemon for ORC control
        self.remote = remote

        # objects
        self.blog = beelog
        self._input_mng = input_mng
        self.stm = TranslatorMethods(beefile=self._beefile,
                                     task_name=self._task_name, beelog=self.blog,
                                     bldaemon=self.remote, job_id=None)

        # AWS configuration
        self.ec2_client = boto3.client('ec2')
        self.efs_client = boto3.client('efs')
        self.__bee_aws_sgroup = '{0}-{1}-bee-aws-security-group'.format(
            self.__user, self._task_name)
        self.__bee_aws_pgroup = '{0}-{1}-bee-aws-placement-group'.format(
            self.__user, self._task_name)
        self.__bee_aws_sgroup_description = 'Security group for BEE-AWS instances.'

    ###########################################################################
    # Adapter functions
    # orc_translator.py & launch_translator.py
    ###########################################################################
    def specific_allocate(self, test_only=False, dependency=None):
        """
        Create sbatch file utilizing Beefile's defined 'requirements' then
        execute this sbatch via subprocess.
        At this moment this system must be run on the login node of the cluster
        :return: unique job id associated with successful allocation
        """
        tmp_f = NamedTemporaryFile()
        tmp_f.write(bytes("#!/bin/bash\n\n", 'UTF-8'))
        if self._beefile_req is not None:
            if self._beefile_req.get('ResourceRequirement') is not None:
                pass
            else:
                self.blog.message("ResourceRequirement key is required for "
                                  "allocation", self._task_name, self.blog.err)
            if self._beefile_req.get('SoftwareModules') is not None:
                pass
            if self._beefile_req.get('EnvVarRequirements') is not None:
                pass
            if self._beefile_req.get('CharliecloudRequirement') is not None:
                pass

        # TODO: re-add bee-orchestrator deploy step

        tmp_f.seek(0)
        self.blog.message(tmp_f.read().decode())

        tmp_f.seek(0)
        out = None
        if not test_only:
            out = None
        tmp_f.close()
        return out

    def specific_shutdown(self, job_id):
        pass

    def specific_move_file(self):
        pass

    def specific_launch(self):
        pass

    def specific_execute(self, command, system=None, capture_out=True):
        if system is not None:
            pass
        else:  # run via ??? (take responsibility)
            pass

    @staticmethod
    def specific_get_jobid():
        pass

    def specific_get_remote_orc(self):
        return self.remote

    def specific_get_nodes(self):
        pass

    ###########################################################################
    # Protected/Private supporting functions
    ###########################################################################
    def __get_bee_instance_ids(self):
        """
        :return: List of all instances in BEE pgroup not yet terminated
        """
        resp = self.ec2_client.describe_instances()
        inst_ids = []
        for rsv in resp['Reservations']:
            for inst in rsv['Instances']:
                if inst['Placement']['GroupName'] == self.__bee_aws_pgroup \
                        and inst['State']['Name'] != 'terminated':
                    inst_ids.append(inst['InstanceId'])
        return inst_ids

    def __get_bee_sg_id(self):
        """
        :return: Get the id of bee security groups, return -1 if not exists
        """
        all_sgs = self.ec2_client.describe_security_groups()
        bee_security_group_id = -1
        for sg in all_sgs.get('SecurityGroups', {}):
            if sg.get('GroupName') == self.__bee_aws_sgroup:
                bee_security_group_id = sg.get('GroupId')
        return bee_security_group_id

    def __is_bee_pg_exist(self):
        """
        :return: Boolean, determine if BEE placement group exists
        """
        all_pgs = self.ec2_client.describe_placement_groups()
        for pg in all_pgs.get('PlacementGroups', {}):
            if pg.get('GroupName', False):
                return True
        return False
