#!/usr/bin/env python

import os
import re
import csv
from mcmtest.lib.helpers import mcmtest_path

pjoin = os.path.join

class LogAnalyzer:
    '''
    Class for analyzing logs of HTCondor test jobs.
    Analyzes the logs for each job separately and extracts
    the following information:
    
    --- Cross-section 
    --- Filter efficiency
    --- Matching efficiency
    --- Time/event value
    --- Size/event value
    
    Dumps the information into a new csv file together
    with prepIDs.
    '''
    def __init__(self, directory):
        '''
        Initialize the LogAnalyzer object. Sets the relevant 
        log files for the analyzer to read, according to 
        specified directory.
        
        ================
        PARAMETERS:
        ================
        directory : The output directory containing the out_*.txt and err_*.txt files.
        '''
        self.directory = mcmtest_path(directory)

        # Initialize and fill the container containing a mapping
        # of prepIDs to its stderr and stdout files. 
        # stdout files contain time/event and size/event values
        # stderr files contain efficiency and x-section
        self._init_container()

    def _init_container(self):
        '''Initialize and fill the container.'''
        self.container = {}

        for f in os.listdir(self.directory):
            if not f.startswith('out'):
                continue
            
            prepid = f.strip('out_').strip('.txt')
            self.container[prepid] = {'prepid' : prepid}
            
        for prepid in self.container.keys():
            err_file = pjoin(self.directory, f'err_{prepid}.txt')
            if not os.path.exists(err_file):
                raise FileNotFoundError(f'Stderr file not found: {err_file}')
        
            out_file = pjoin(self.directory, f'out_{prepid}.txt')
            if not os.path.exists(out_file):
                raise FileNotFoundError(f'Stdout file not found: {out_file}')
    
            self.container[prepid]['stderr'] = err_file    
            self.container[prepid]['stdout'] = out_file    

    def _get_from_stdout(self):
        '''Get the time/event and size/event values for each request from stdout.
           Append the values to the container.'''
        for prepid in self.container.keys():
            out_file = self.container[prepid]['stdout']    
            with open(out_file, 'r') as f:
                size_event_found = False
                time_event_found = False
                # Scan the file and find the lines containing 
                # time/event and size/event values.
                # Files are large, hopefully this approach doesn't
                # use unneccessary memory.
                for line in f:
                    if line.startswith('McM Size/event'):
                        size_event = float( re.findall('\d+.\d+', line)[0] )
                        self.container[prepid]['Size per event'] = size_event
                        size_event_found = True
                    if line.startswith('McM time_event'):
                        time_event = float( re.findall('\d+.\d+', line)[0] )
                        self.container[prepid]['Time per event'] = time_event
                        time_event_found = True
                
                # Issue warning if size/event or time/event values are not found
                # For now, set the values to be zero if they are not found
                if not size_event_found:
                    print(f'WARNING: Size/event for {prepid} not found, setting to 0')
                    self.container[prepid]['Size per event'] = 0
                if not time_event_found:
                    print(f'WARNING: Time/event for {prepid} not found, setting to 0')
                    self.container[prepid]['Time per event'] = 0
    
    def _get_from_stderr(self):
        '''Get x-section value for each request from logs.
              Append the values to the container.'''
        for prepid in self.container.keys():
            # x-sections stored in stderr 
            err_file = self.container[prepid]['stderr']
            with open(err_file, 'r') as f:
                xs_found = False
                filtereff_found = False
                matcheff_found = False
                # Scan the file and find the final value of x-section
                # after matching and filtering
                search_pat_xs = 'After filter: final cross section'
                search_pat_filtereff = 'Filter efficiency (event-level)'
                search_pat_matcheff = 'Matching efficiency' 
                for line in f:
                    if line.startswith(search_pat_xs):
                        xsec = float(
                                     re.findall('\d+.\d+e?[+-]?\d+', line)[0] 
                                    )    
                        self.container[prepid]['Cross section (pb)'] = xsec
                        xs_found = True

                    elif line.startswith(search_pat_filtereff):
                        filtereff = float( 
                                          re.findall('\d+.\d+', line)[0] 
                                         )    
                        self.container[prepid]['Filter efficiency'] = filtereff
                        filtereff_found = True

                    elif line.startswith(search_pat_matcheff):
                        matcheff = float( 
                                         re.findall('\d+.\d+', line)[0] 
                                        )    
                        self.container[prepid]['Match efficiency'] = matcheff
                        matcheff_found = True
    
                # Issue warning if x-sec or filter/matching efficiency values are not found
                # For now, set the values to be zero if they are not found
                if not xs_found:
                    print(f'WARNING: Cross section for {prepid} not found, setting to 0')
                    self.container[prepid]['Cross section (pb)'] = 0
                if not filtereff_found:
                    print(f'WARNING: Filter efficiency for {prepid} not found, setting to 0')
                    self.container[prepid]['Filter efficiency'] = 0
                if not matcheff_found:
                    print(f'WARNING: Matching efficiency for {prepid} not found, setting to 0')
                    self.container[prepid]['Match efficiency'] = 0

    def dump_to_csv(self, csvfile):
        '''Gets all the values for all requests, and dumps the content to a csv file.''' 
        # Get values from stdout and stderr
        self._get_from_stdout()
        self._get_from_stderr()

        # Dump the contents of the main container into the csv file
        with open(csvfile, 'w+') as f:
            fieldnames = ['prepid', 'Cross section (pb)', 'Filter efficiency', 'Match efficiency', 'Time per event', 'Size per event']
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for data in self.container.values():
                writer.writerow(data)        

        print(f'CSV file saved: {csvfile}')

        
