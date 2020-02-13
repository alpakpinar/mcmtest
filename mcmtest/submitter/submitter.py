import htcondor
import os
import sys
from pprint import pprint
from mcmtest.lib.helpers import copy_proxy
from mcmtest.lib.condor import condor_submit

pjoin = os.path.join

class Submitter:
	'''
	HTCondor submitter for a list of McMPrepIDs.
	Provided the prepID list, adjusts the relevant settings
	(proxy, file_transfer etc.) and submits all test jobs to HTCondor.

	Example usage:
	>>> sub = Submitter(prepid_list=<PrepID_list>)
	
	Get the submission settings for the requests:
	>>> sub.submission_settings

	Submit all jobs to HTCondor:
	>>> sub.submit()
	'''
	def __init__(self, prepid_list):
		'''Initializer function for the Submitter class.
		   Initializes the submission settings for HTCondor.

		   ================
		   PARAMETERS
		   ================
		   prepid_list : The list of McM PrepIDs that are being tested.
		'''
		self.prepid_list = prepid_list
	
		executable = '/afs/cern.ch/user/a/aakpinar/mcmtest/mcmtest/execute/run_test.sh'
	
		# Initialize submission settings 
		# for HTCondor
		self.submission_settings = {
			'universe' : 'vanilla',
			'executable' : executable, 
			'should_transfer_files' : 'YES',
			'transfer_output_files' : '""',
			# Run jobs only on SLC6 
			'requirements' : '(OpSysAndVer =?= "SLCern6")',
			# Maximum run-time: 2 hours
			'+JobFlavour'  : 'longlunch' 
		}
		# Copy the VOMS proxy file to AFS
		# and get the new path to it	
		proxy_path = copy_proxy()
		self.submission_settings['proxy_path'] = proxy_path
	
		# Transfer the VOMS proxy file to HTCondor
		self.submission_settings['transfer_input_files'] = proxy_path

	def submit(self):	
		'''Submit the test jobs for all prepIDs to HTCondor.'''
		for prepid in self.prepid_list:
			# Set the correct arguments for the executable
			arg_list = ['$(proxy_path)', prepid]
			args = ' '.join(arg_list)		
			self.submission_settings['arguments'] = args

			# Set output log files
			outdir=os.path.expanduser('~/mcm_testarea/output/')
			if not os.path.exists(outdir):
				os.makedirs(outdir)
			output_file = pjoin(outdir, 'out_{0}.txt'.format(prepid))
			log_file = pjoin(outdir, 'log_{0}.txt'.format(prepid))
			err_file = pjoin(outdir, 'err_{0}.txt'.format(prepid))

			self.submission_settings['output'] = output_file
			self.submission_settings['log'] = log_file
			self.submission_settings['error'] = err_file

			sub = htcondor.Submit(self.submission_settings)

			# Write the job file to submit
			jobfiledir = os.path.expanduser('~/mcm_testarea/job_files')
			if not os.path.exists(jobfiledir):
				os.makedirs(jobfiledir)

			jobfile = pjoin(jobfiledir, 'job_{0}.jdl'.format(prepid))
			with open(jobfile, 'w+') as f:
				f.write(str(sub))
				f.write('\nqueue 1\n')

			# Submit the job
			jobid = condor_submit(jobfile)
			print('Submitted job: {0}, Job ID: {1}'.format(prepid, jobid))


