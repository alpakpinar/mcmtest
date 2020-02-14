import os
import pickle
import htcondor
from mcmtest.lib.condor import CondorJob

pjoin = os.path.join

def read_logs(directories):
    '''Read the log files in a given list of directories.'''
    logs = []
    for directory in directories:
        for path, _, files in os.walk(directory):
            logs.extend([os.path.join(path, x) for x in files if x.startswith("log_")])
    return logs

class LogManager:
    '''Class for wrapping a list of condor jobs in the given directory.'''
    def __init__(self, directory):
        self.directory = directory
        # Each log manager is assigned a cache file: "jobs.pkl"
        self.pkl = pjoin(directory, 'jobs.pkl')
        self.autoresub = False
        
        # Load from the cache if it already exists
        if os.path.exists(self.pkl):
            self.jobs = pickle.load( open(self.pkl, 'rb') )

        else:
            self.init_jobs()

    @property
    def directory(self):
        return self._directory

    @directory.setter
    def directory(self, directory):
        directory = os.path.abspath(directory)
        if not os.path.exists(directory):
            raise FileNotFoundError(f'Directory not found: {directory}')
        self._directory = directory

    @property
    def jobs(self):
        return self._jobs

    @jobs.setter
    def jobs(self, jobs):
        self._jobs = sorted(jobs, key=lambda x: x.name)

    @property
    def autoresub(self):
        return self._autoresub

    @autoresub.setter
    def autoresub(self, autoresub):
        self._autoresub = autoresub

    def init_jobs(self):
        '''Initiate the jobs by looking at each log file 
           in the relevant directory.'''
        logs = read_logs([self.directory])
        # Create a CondorJob object for each job
        jobs = list( map(CondorJob, logs) )
        self.jobs = jobs
    
    def update(self):
        '''Update job status for each job in the log.
           Resubmit failed jobs, until resubmission count 
           reaches the maximum.'''
        for job in self.jobs:
            job.update()
        if self.autoresub:
            self.resubmit_failed(max_resub=3)

    def resubmit_failed(self, max_resub=None):
        '''Resubmit failed jobs until the resubmission count
           reaches the maximum resubmission count specified.
           Returns the number of jobs that are resubmitted.'''
        jobcount = 0
        for job in self.jobs:
            # Look for job termination with non-zero return code.
            # Skip the cases in which information about job was not available.
            # (Job code: '-')
            if (not job.code in [0, '-']) or (job.status == 'JOB_ABORTED'):
                if max_resub and max_resub <= job.resubcount:
                    continue
                job.resubmit() 
                jobcount += 1
        
        return jobcount

    def save(self):
        '''Save contents into a .pkl file.'''
        pickle.dump( self.jobs, open(self.pkl, 'wb')  )







        
