import subprocess
import re
import shutil
import os
import mcmtest

pjoin = os.path.join

def mcmtest_path(path_to_file):
	return pjoin(mcmtest.__path__[0], path_to_file)

def voms_proxy_path():
	'''Get the path where VOMS proxy file is stored.'''
	cmd = ['voms-proxy-info']
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

	stdout, _ = proc.communicate()
	if proc.returncode != 0 :
		raise RuntimeError("Could not run voms-proxy-info command.")
	
	pathline = [x for x in stdout.decode('utf-8').split('\n') if x.startswith('path')]
	proxy_path = re.sub('.* /', '/', pathline[0])
	return proxy_path

def copy_proxy():
	'''Copy the proxy file to .voms/ directory in mcm_testarea.
	   Returns the new path to the proxy file.'''
	proxy_path = voms_proxy_path()
	proxy_dir = os.path.expanduser('~/mcm_testarea/.voms/')
	if not os.path.exists(proxy_dir):
		os.makedirs(proxy_dir)
	shutil.copy2(proxy_path, proxy_dir)

	new_proxy_path = os.path.join(proxy_dir, os.path.basename(proxy_path))
	return new_proxy_path

	
