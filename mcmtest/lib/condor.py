import os
import subprocess
import htcondor

def condor_submit(jobfile):	
	'''Execute condor submission, return the assigned job ID.'''
	cmd = ['condor_submit', jobfile]
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

	stdout, stderr = proc.communicate()
	if proc.returncode != 0:
		raise RuntimeError(f'Condor submission failed: {stderr}')

	jobid = stdout.split()[-1].decode('utf-8').replace('.','')
	return jobid

def read_logs(directories):
	'''Read the log files in a given list of directories.'''
	logs = []
	for directory in directories:
		for path, _, files in os.walk(directory):
			logs.extend([os.path.join(path, x) for x in files if x.startswith("log_")])
	return logs

class CondorJob:
	'''Wrapper for a HTCondor job.'''
	def __init__(self, log):
		self.log = log
		self.status = None
		self.name = os.path.basename(self.log).replace('log_','').replace('.txt','')
		self.resubcount = 0
		self.update()

	@property
	def log(self):
		return self._log

	@log.setter
	def log(self,log):
		log = os.path.abspath(log)
		if not os.path.exists(log):
			raise FileNotFoundError(f'File not found: {log}')
		self._log = log

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self, name):
		self._name = name

	@property
	def status(self):
		return self._status

	@status.setter
	def status(self, status):
		self._status = status
	 	
	@property
	def code(self):
		return self._code

	@code.setter
	def code(self, code):
		self._code = code

	@property
	def cluster(self):
		return self._cluster

	@cluster.setter
	def cluster(self, cluster):
		self._cluster = cluster
	
	@property
	def resubcount(self):
		return self._resubcount

	@resubcount.setter
	def resubcount(self, resubcount):
		self._resubcount = resubcount
	
	@property
	def runtime(self):
		return self._runtime

	@runtime.setter
	def runtime(self, runtime):
		self._runtime = runtime

	def update(self):
		if self.status == 'JOB_TERMINATED':
			return
		
		# For updaing, open the log file
		# and look at the status of the 
		# last event.
		jel = htcondor.JobEventLog(self._log)

		first = None
		try:
			for event in jel.events(stop_after=0):
				if not first:
					first = event
				latest = event
			try:
				self.code = latest['ReturnValue']
			except KeyError:
				self.code = '-'
			self.status = str(htcondor.JobEventType.values[latest.type])
			self.cluster = latest.cluster
			self.runtime = latest.timestamp - first.timestamp

		except OSError:
			self.code = '-'
			self.status = 'NOPARSE'
			self.cluster = '-'
			self.runtime = -1

		finally:
			jel.close()

	def to_jdl(self):
		return self.log.replace('log_','job_').replace('.txt', '.jdl')

	def resubmit(self):
		self.status = None
		condor_submit(self.to_jdl())
		self.resubcount += 1





			
		


  		



	

