#!/usr/bin/env python

""" 
 Script for generating dname redirection (fallback scenario with 'dname') for named.conf
 Parameters : (<GS1 prefixes filename>, <local ons>, [<default ons>]) 
"""

import sys
import string

# usage
if len(sys.argv) < 3:
    print "Usage : ", sys.argv[0], "<filename> <local ons> [<default ons>]"
    sys.exit()

# get parameters
prefixes_list = {}
filename = sys.argv[1]
local_ons = sys.argv[2]
if len(sys.argv) == 4:
    default_ons = sys.argv[3]
else:
    default_ons = ''

print "; DNAME redirections for " + local_ons
print

# read GS1 prefixes in a text file, populate the prefixes list table 
file_reader = open(sys.path[0] + '/' + filename, 'r')

for line in file_reader:
    line = line.strip() # remove trailing "\n"
    if line == '' or line[0] == '#' or line[0] == '//' or line[0] == ';' :
        continue # ignore comments line
    # print "==>", line

    (gs1_prefixes, comment, ons) = line.split(':')
   
    # get GS1 range (if exists in the textfile)
    if gs1_prefixes.find('-') > 0:
        (start_prefix, end_prefix) = gs1_prefixes.split('-')
    else:
        start_prefix = gs1_prefixes
        end_prefix = gs1_prefixes

    # loop on all prefixes
    for i in range(int(start_prefix), int(end_prefix) + 1) :
        if ons == 'default':
            ons = default_ons
        prefixes_list[i] = [ ons, comment ]

file_reader.close()

# final output to include in a zone file
for i in range(0, 999):
    prefix = [] + list("%03d"%i) # prefix on 3 digits
    prefix = prefix[::-1] # invert prefix
    str = '.'.join(prefix) + '.id.' + local_ons + '. IN DNAME ' + '.'.join(prefix) + '.id.%s.' + ' ;%s'

    if prefixes_list.has_key(i) :
        # format dname line for existing prefixes
        (ons, comment) = prefixes_list[i] 
        if local_ons != ons: # avoid loop or wrong dname
            print str%(ons, comment)
    else :
        # format dname line for default rule
        if default_ons != '' and default_ons != local_ons : # avoid loop or wrong dname
            print str%(default_ons, 'default rule')
