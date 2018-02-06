#!/usr/bin/env python

# script for Generating URN in a random manner
# URI format : urn:epc:id:sgtin:CompanyPrefix.ItemReference
# Example urn:epc:id:sgtin:3004567.436757
####

import random, getopt, sys, os, string
import libepcconvert

def usage() :
    print
    print "Usage : " + sys.argv[0] + " [options]"
    print "options :"
    print "  -h, --help         show this help"
    print "  -n, --count        number of generated URN"
    print "  -l, --gcp-length   length of randomized GCP"
    print "  -g, --gcp          set GCP for generated URN"
    print "  -p, --itemref      initial item reference (and increments the others)"
    print "  -i, --increment    increment for item reference (defaut=1)"
    print "  -x, --with-hexa    print the hexa value"
    print "  -b, --barcode      generate GTIN instead of EPC"
    print "  -o, --ons-levels   total of ONS levels : 3,2,1 (Root, Country, Local)"
    print "  -t, --service-type set the service type"
    print "  -u, --service-uri  set the URI for the service"
    print "  -s, --service-random-uri set a randomized URI for the service"
    print


# Main
# Generate random URNs
def main(argv=None):
    if argv is None:
        argv = sys.argv

    output = []
    code_type="sgtin"
    cnt = 10
    gcp_length = 7
    gcp = ""
    itemref = ""
    serialnum = "100"
    incr = 1

    with_hexa_value = False
    ons_levels = ""
    service_type = "epc+html"
    service_uri = ""
    service_random_uri = False

    # read options from the command line and override previous values                                                             

    try :
        opts, args = getopt.getopt(argv[1:], 
                "hn:l:g:p:i:xo:t:u:sb", 
                ["help", "count=", "gcp-length=", "gcp=", "itemref=", "increment=", 
                "with-hexa", "ons-levels""service-type", "service-uri", "service-random-uri",  "barcode"])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)    

    for option, value in opts :
        if option in ["-h", "--help"] :
            usage()
            sys.exit(0)
        elif option in ["-n", "--count"] :
            cnt = int(value)
        elif option in ["-l", "--gcp-length"] :
            gcp_length = int(value)
        elif option in ["-g", "--gcp"] :
            gcp = value
        elif option in ["-p", "--itemref"] :
            itemref = value
        elif option in ["-i", "--increment"] :
            incr = int(value)
        elif option in ["-x", "--with-hexa"] :
            with_hexa_value = True 
        elif option in ["-o", "--ons-levels"] :
            ons_levels = value 
        elif option in ["-t", "--service-type"] :
            service_type = value.lower()
        elif option in ["-u", "--service-uri"] :
            service_uri = value.lower()
        elif option in ["-s", "--service-random-uri"] :
            service_random_uri = True 
        elif option in ["-b", "--barcode"] :
            code_type = "gtin"

    j = 0
    while cnt > 0 :

        output_line = ""
        if code_type == "sgtin" :
            i = 0 
            urn = "urn:epc:id:sgtin:"

            if gcp != "" :
                urn = urn + gcp
                gcp_length = len(gcp)
                i = i + gcp_length

            while i < 13 : 
                if i == (gcp_length) :
                    urn = urn + "."
                    if itemref != "" :
                        urn = urn + str(int(itemref)+j)
                        j = j + incr
                        i = i + len(itemref)
                        continue 
                urn = urn + str(random.randrange(0,9))
                i = i + 1
        
            urn = urn + "." + serialnum

            output_line = urn

            if with_hexa_value :
                output_line = output_line + ";" + libepcconvert.epc_urn2hexa(urn)


        elif code_type == "gtin" :
            cnt = 0 # break loop
            urn = "gtin:" + gcp + "." + itemref
            output_line = urn

        if ons_levels != "" :
            output_line = output_line + "|" + ons_levels

        if service_uri != "" :
            output_line = output_line + "|" + service_type + ";" 
            if (service_uri[0] != "<" or service_uri[-1] != ">") : 
                service_uri = "<" + service_uri + ">"
            output_line = output_line + service_uri
        elif service_random_uri :
            output_line = output_line + "|" + service_type 
            for i in range(random.randint(1, 3)) :
                output_line = output_line + ";"
                random_uri = "<http://www." 
                length = random.randint(8, 13)
                letters = string.ascii_letters 
                random_uri = random_uri + ''.join([random.choice(letters.lower()) for _ in range(length)])  
                random_uri = random_uri + ".org/ons-products/" + string.rsplit(urn, ':', 1)[-1] + ">"
                output_line = output_line + random_uri

        output.append(output_line)
        cnt = cnt - 1

    return output


if __name__ == "__main__":
    output = main()
    for line in output :
        print line
