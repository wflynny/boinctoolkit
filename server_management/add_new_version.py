#!/usr/bin/env python
import os
import re
import sys
import glob
import shutil

def add_new_version():
    usage = "./add_new_version.py  <appname>  <new_version_no>"
    if len(sys.argv) != 3:
        print usage
        sys.exit(1)

    appname, new_no = sys.argv[1:]

    # specify project path
    projectpath = ''
    if not projectpath:
        print "Specify project path in code!"
        sys.exit(1)

    apppath = os.path.join(projectpath, 'apps',  appname)
    if os.path.exists(apppath):
        os.chdir(apppath)

    dirs = sorted([float(d) for d in os.listdir('.') if d[0] in map(str, range(10))])
    src = str(dirs[-1])

    shutil.copytree(src, new_no)
    os.chdir(new_no)

    for filename in glob.glob("*/*"):
	newfilename = filename.replace(src, new_no)

	base, ext = os.path.splitext(filename)
	# edit file
        if ext == '.xml':
	    try:
		with open(filename, 'r') as inf:
                    file_contents = inf.read()
                with open(filename, 'w') as outf:
                    outf.write(file_contents.replace(src, new_no))
	    except:
		print "ERROR: couldn't replace contents of file: %s"%filename
        try:
            os.rename(filename, newfilename)
        except:
            print "ERROR: couldn't move file: %s"%filename

if __name__ == "__main__":
    add_new_version()
