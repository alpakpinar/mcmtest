import subprocess
import htcondor

def condor_submit(jobfile):	
	'''Execute condor submission, return the assigned job ID.'''
	cmd = ['condor_submit', jobfile]
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

	stdout, stderr = proc.communicate()
	if proc.returncode != 0:
		raise RuntimeError('Condor submission failed: {0}'.format(stderr))

	jobid = stdout.split()[-1].decode('utf-8').replace('.','')
	return jobid

	

