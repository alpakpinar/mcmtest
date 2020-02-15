import htcondor
import os
import sys
import re
import numpy as np
from pprint import pprint
from mcmtest.lib.helpers import copy_proxy, mcmtest_path
from mcmtest.lib.condor import condor_submit

pjoin = os.path.join

class Submitter:
    '''
    HTCondor submitter for a list of McM prepIDs.
    Provided the prepID list, adjusts the relevant settings
    (proxy, file_transfer etc.) and submits all test jobs to HTCondor.

    Example usage:
    >>> sub = Submitter(prepid_list=<PrepID_list>)
    
    Get the submission settings for the requests:
    >>> sub.submission_settings

    Submit all jobs to HTCondor:
    >>> sub.submit()
    '''
    def __init__(self, prepid_list, node_os='centos7', multiple_campaigns=False, dryrun=False):
        '''Initializer function for the Submitter class.
           Initializes the submission settings for HTCondor.

           ================
           PARAMETERS
           ================
           prepid_list : The list of McM PrepIDs that are being tested.
           node_os     : The desired operating system in the work nodes.
                         The default OS is CentOS 7 (defualt OS HTCondor submits to), 
                         but Submitter also accepts Scientific Linux 6 (node_os=slc6).
           multiple_campaigns : Set True if multiple campaigns are to be submitted at one go.
                                Otherwise, set False (default behavior). 
           dryrun      : Dry run. No submissions will be made, information about prepID-campaign
                         mapping will be printed to the screen.
        '''
        self.prepid_list = prepid_list
        self.multiple_campaigns = multiple_campaigns
        self.dryrun = dryrun    

        executable = '/afs/cern.ch/user/a/aakpinar/mcmtest/mcmtest/execute/run_test.sh'
    
        # Initialize submission settings 
        # for HTCondor
        self.submission_settings = {
            'universe' : 'vanilla',
            'executable' : executable, 
            'should_transfer_files' : 'YES',
            'transfer_output_files' : '""',
            # Maximum run-time: 4 hours
            '+MaxRuntime'  : f'{60*60*4}' 
        }
        # If SLC6 OS is specified, add it to submission settings
        if node_os == 'slc6':
            self.submission_settings['requirements'] = '(OpSysAndVer =?= "SLCern6")'
        
        if node_os not in ['slc6', 'centos7']:
            raise ValueError('Invalid value for node_os: Use centos7 or slc6.')

        # Copy the VOMS proxy file to AFS
        # and get the new path to it    
        proxy_path = copy_proxy()
        self.submission_settings['proxy_path'] = proxy_path
    
        # Transfer the VOMS proxy file to HTCondor
        self.submission_settings['transfer_input_files'] = proxy_path

    def _get_campaign_name(self):
        '''Get the campaign name(s) from given prepIDs.'''
        get_campaign = lambda x : '-'.join(x.split('-')[:-1])
        
        # Case for a single campaign submission
        if not self.multiple_campaigns:
            prepid = self.prepid_list[0]
            campaign_name_list = list(get_campaign(prepid))
    
        # Handle if multiple campaigns are to be submitted at once
        else:
            campaign_names_all = list( map(get_campaign, self.prepid_list) )
            campaign_name_list = np.unique(campaign_names_all)

        return campaign_name_list

    def _get_prepid_campaign_map(self):
        '''Get a mapping of prepIDs to their relevant campaigns.'''
        campaign_name_list = self._get_campaign_name()
        prepid_campaign_map = {}

        for campaign_name in campaign_name_list:
            prepid_campaign_map[campaign_name] = []
            for prepid in self.prepid_list:
                if re.match(f'{campaign_name}-.*', prepid):
                    prepid_campaign_map[campaign_name].append(prepid)

        return prepid_campaign_map

    def submit(self):    
        '''Submit the test jobs for all prepIDs to HTCondor.'''
        prepid_campaign_map = self._get_prepid_campaign_map()

        for campaign_name, prepids in prepid_campaign_map.items():       
            # Set output directory for each campaign
            outdir = mcmtest_path(f'output/{campaign_name}')
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            
            jobfiledir = mcmtest_path(f'job_files/{campaign_name}') 
            if not os.path.exists(jobfiledir):
                os.makedirs(jobfiledir)
            
            for prepid in prepids:
                # Set the correct arguments for the executable
                arg_list = ['$(proxy_path)', prepid]
                args = ' '.join(arg_list)        
                self.submission_settings['arguments'] = args

                # Set output log files
                output_file = pjoin(outdir, f'out_{prepid}.txt')
                log_file = pjoin(outdir, f'log_{prepid}.txt')
                err_file = pjoin(outdir, f'err_{prepid}.txt')

                self.submission_settings['output'] = output_file
                self.submission_settings['log'] = log_file
                self.submission_settings['error'] = err_file

                sub = htcondor.Submit(self.submission_settings)

                # Write the job file to submit
                jobfile = pjoin(jobfiledir, f'job_{prepid}.jdl')
                with open(jobfile, 'w+') as f:
                    f.write(str(sub))
                    f.write('\nqueue 1\n')

                # Submit the job, if dry run is not specified
                if not self.dryrun:
                    jobid = condor_submit(jobfile)
                    print(f'Submitted job: {prepid}, Job ID: {jobid}')
        
        if self.dryrun:
            print('Dry run requested. No submissions will be made.')
            print('PrepID and campaign information:')
            pprint(prepid_campaign_map)




