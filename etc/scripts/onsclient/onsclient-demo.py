#!/usr/bin/env python

####
# ONS client application (script for testing Federated ONS)
# AFNIC R&D 2010
####

import libonsclient

import time
import os
import sys
import webbrowser
import getopt
import ConfigParser

#
# User callback (what to do with the URL retreived from ONS)
#
def go_to_url(url) :
    print_info("=> Action : launching web browser...")
    try :
        # firefox = webbrowser.get('firefox')
        # firefox.open_new_tab(url) 
    
        webbrowser.open_new_tab(url)
    except webbrowser.Error:
        print "Web browser error !"

#
# Query ONS with a GS1 Identifier
#
def query_ons(gs1_code) :
    # ONS resolution
    url = libonsclient.code2url(gs1_code, opt_ons_root, opt_name_server, opt_service_type)
        
    # result
    if len(url) != 0 :
        if opt_quiet :
            print url
        if opt_open_browser :
            go_to_url(url) 

#
# Output : overload libonsclient's print_info function
#
def print_info(str):
    if not opt_quiet :
        print str
        print

libonsclient.print_info = print_info

#
# Usage function for this script
#
def usage() :
    print
    print "Usage : " + sys.argv[0] + " [options]" 
    print "options :"
    print "   -h, --help           show this help"
    print "   -q, --quiet          quiet mode, no resolution information" 
    print "   -b, --open-browser   open final url in the default web browser"
    print "   -c, --code           EPC (24 hexa), barcode (GTIN-13) or URN-EPC"
    print "   -p, --peer-root      Peer ONS root (domain name, e.g. onsepc1.eu)"
    print "   -f, --epc-inputfile    read EPC codes from text file"
    print "   -l, --epc-inputlogfile read EPC codes from log text file (watch log)"
    print "   -s, --name-server     local ONS resolver queried"
    print "   -t, --service-type   service type selected for NAPTR record"
    print "See config file (onsclient-resolv.conf) for default options"
    print

####
# Main function
####
if __name__ == "__main__":

    # default options 
    opt_quiet = False
    opt_open_browser = False 
    opt_gs1_code = ""
    opt_gs1_code_type = ""
    opt_ons_root = ""
    opt_epc_inputfile = ""
    opt_epc_inputlogfile = ""
    opt_name_server = ""
    opt_service_type = ""
    
    try:
        # read default options in the config file
        conf_options = ConfigParser.ConfigParser()
        conf_options.read(os.path.dirname(sys.argv[0]) + "/onsclient-resolv.conf")
        for option, value in conf_options.items("default") :
            if option == "quiet" :
                if value.lower() == "yes" :
                    opt_quiet = True 
            elif option == "open-browser" :
                if value.lower() == "yes" :
                    opt_open_browser = True
            elif option == "ons-root" :
                opt_ons_root = value
            elif option == "epc-inputlogfile" :
                opt_epc_inputlogfile = value
            elif option == "epc-inputfile" :
                opt_epc_inputfile = value
            elif option == "name-server" :
                opt_name_server = value
            elif option == "service-type" :
                opt_service_type = value.lower()

        # read options from the command line and override previous values
        opts, args = getopt.getopt(sys.argv[1:], "hqbc:p:l:f:s:t:", 
                ["help", "quiet", "open-browser", "code=", "ons-root=", 
                    "epc-inputlogfile=", "epc-inputfile=", "ns=", "service-type="])

        for option, value in opts :
            if option in ["-q", "--quiet"]:
                opt_quiet = True 
            elif option in ["-b", "--open-browser"]:
                opt_open_browser = True 
            elif option in ["-c", "--code"]:
                opt_gs1_code = value
                opt_gs1_code_type = "gtin-13" # type_of_gs1_code(opt_gs1_code)
                if opt_gs1_code_type == "" :
                    raise getopt.GetoptError, "GS1 code type not supported !"
            elif option in ["-p", "--ons-root"]:
                opt_ons_root = value
            elif option in ["-l", "--epc-inputlogfile"]:
                opt_epc_inputlogfile = value
            elif option in ["-f", "--epc-inputfile"]:
                opt_epc_inputfile = value
            elif option in ["-s", "--name-server"]:
                opt_name_server = value
            elif option in ["-t", "--service-type"]:
                opt_service_type = value
            else : 
                usage()
                sys.exit(0)

        if opt_ons_root == "" :
            raise getopt.GetoptError, "ONS root option missing !" 

    except getopt.GetoptError, err:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    
    fd = False

    print "Configuration : service=" + opt_service_type + ", name server=" + opt_name_server + ", ONS Root=" + opt_ons_root


    # launch ONS resolution
    if opt_gs1_code != "" : 
        query_ons(opt_gs1_code)
        sys.exit(0)

    # else interactive mode (waiting for EPC inputs)
    try :
        # read EPC in a text file
        if opt_epc_inputfile != "" :
            print "Reading inputs from file '" + opt_epc_inputfile + "'\n"
            fd = open(opt_epc_inputfile, "r")

            for line in fd :
                gs1_code = line.strip() # remove trailing "\n"
                if gs1_code == "" or gs1_code[0] == '#' : # jump comments line
                    continue
                else :
                   query_ons(gs1_code) 

        # Read EPC from log file (from RFID reader's log)
        elif opt_epc_inputlogfile != "" :
            fd = open(opt_epc_inputlogfile, "r")
            print "Waiting for inputs from file '" + opt_epc_inputlogfile + "'\n"

            # Watch log file (updates)
            save_mt = os.fstat(fd.fileno()).st_mtime
            while 1:
                st = os.fstat(fd.fileno())
                if st.st_mtime > save_mt:
                    save_mt = st.st_mtime
    
                    # extract EPC code
                    fd.seek(0)
                    data = fd.readlines()
                    str = data[len(data)-1]
                    query_ons(str[:24])

                time.sleep(0.2)

        # watch stdin (keyboard, barcode reader, 2D reader...) and loop 
        else :
            while 1:
                # ONS resolution
                query_ons(raw_input("GS1 code : "))

    except IOError:
        print "RFID/EPC file not found !"
        sys.exit(0)

    except KeyboardInterrupt: 
        if fd :
            fd.close()
        sys.exit(0)

    except EOFError:
        sys.exit(0)
