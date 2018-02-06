#!/usr/bin/env python

import getopt, sys, re
import libepcconvert


def usage() :
    print
    print "Usage : " + sys.argv[0] + " <epc-urn>|<epc-hexa-24>"
    print "options :"
    print "  -h, --help   show this help"
    print "Convert from URN to Hexa (and vice versa)"
    print


def main() :
    

    code = ""

    try :
        # read options from the command line and override previous values 
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"]) 

        for option, value in opts :
            if option in ["-h", "--help"] :
                usage()
                sys.exit(0)

    except getopt.GetoptError, err:
        print str(err) 
        usage()
        sys.exit(2)

    if len(sys.argv) > 1 :
        code = sys.argv[1]

    if code == "" :
        usage()
        sys.exit(2)

    if re.search(re.compile("^[A-F0-9]{24}$"), code.upper()) :
        # Hexa value 
        urn_value = libepcconvert.epc_hexa2urn(code)
        print "URN value : " + urn_value 
    else :
        # URN value
        hexa_value = libepcconvert.epc_urn2hexa(code)
        print "Hexa value : " + hexa_value + " (" + str(len(hexa_value)) + " digits)"


if __name__ == "__main__": 
    main()
