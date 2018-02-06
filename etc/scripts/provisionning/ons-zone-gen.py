#!/usr/bin/env python
import getopt, sys, re, random, os, string, shutil, ConfigParser
from datetime import date

import random_epcgen

#
# Initialize a working directory
#
def init_dir() :

    os.system("rm -rf %s.old" % opt_gen['working_directory'])
    os.system("if [ -d %s ]; then mv %s %s.old; echo '  working directory backup...'; fi" 
        % (opt_gen['working_directory'], opt_gen['working_directory'], opt_gen['working_directory']))
    os.system("mkdir %s" % opt_gen['working_directory'])
    os.system("mkdir %s/root-ons" % opt_gen['working_directory'])
    os.system("mkdir %s/country-ons" % opt_gen['working_directory'])
    os.system("mkdir %s/local-ons" % opt_gen['working_directory'])
    os.system("mkdir %s/dlocal-ons" % opt_gen['working_directory'])


#
# Generate EPC URNs in a file
#
def epc_urn_gen() :
    
    gcp_list = [] 

    for gs1_prefix in opt_gen['gs1_prefix'].split(',') : # 3 digits
        company_code = random.randrange(int(opt_gen['min_company']), int(opt_gen['max_company'])-int(opt_gen['nb_gcp'])) # 4 digits
        for i in range(0, int(opt_gen['nb_gcp'])) :
            gcp_list.append(gs1_prefix + str(company_code + i)) # GCPs with 7 digits

    urn_list = []
    for gcp in gcp_list :
        itemref = random.randrange(int(opt_gen['min_itemref']), int(opt_gen['max_itemref'])-int(opt_gen['nb_prod'])) # 6 digits
        urn_list = urn_list + random_epcgen.main(['random_epcgen.py', '-n', opt_gen['nb_prod'], '-g', gcp, '-p', str(itemref), '-o', opt_gen['ons_levels'], '-s'])

        # log out
        sys.stdout.write("#%d\r" % len(urn_list))
        sys.stdout.flush()

    urn_file = open('%s/urn.txt' % opt_gen['working_directory'], 'a')
    for urn in urn_list :
        urn_file.write(urn + '\n')
    urn_file.close()

    count_file = open('%s/count.txt' % opt_gen['working_directory'], 'a')
    count_file.write('** Number of GS1 prefixes : %d\n' % len(opt_gen['gs1_prefix'].split(',')))
    if len(opt_gen['gs1_prefix'].split(',')) < 100 :
        count_file.write('%s\n\n' % str(opt_gen['gs1_prefix']))
    count_file.write('Number of GCP generated : %d (each with %s products) \n' % (len(gcp_list), opt_gen['nb_prod']))
    if len(gcp_list) < 100 :
        count_file.write('%s\n\n' % str(gcp_list))
    count_file.write('Total of URN generated : %d\n\n' % len(urn_list))
    count_file.close()

#
# Generate zone files and config files correponding to the previous URN file format
# See related script output format (random_epcgen.py)
#
def epc_ons_zone_gen() :

    urn_file = open('%s/urn.txt' % opt_gen['working_directory'], 'r')

    gcp_list = {} # dictionary of all GCPs found
    prefix_list = {} # dictionary all GS1 prefixes found
    ons_levels = {} # dictionary for ONS levels

    count_max = 0

    # read the file and put the data in a dictionary structure (the key is GCP)

    # EPC code regexp
    reg_exp = re.compile("^urn:epc:id:sgtin:(\d{7})\.(\d{6})(.\d+)?(;[\w]{24})?\|([123])\|(.*)$")
    code_type = 'sgtin'

    # barcode regexp 
    reg_exp_bc = re.compile("^gtin:(\d+)\.(.\d+)(.\d+)?(;[\w]{24})?\|([123])\|(.*)$")

    for line in urn_file :
        gcp = ""
        itemref = ""
        serialnum = ""
        gcp_hex = ""
        services_str = ""

        # print "--->" + line.strip() + "<--"

        if  line.find("urn:epc") != -1 :
            # grep EPC URN line
            elements = re.search(reg_exp, line)
        else :
            elements = re.search(reg_exp_bc, line) 
            code_type = 'gtin'

        if elements :
            gcp = elements.group(1)
            itemref = elements.group(2)
            serialnum = elements.group(3)
            gcp_hex = elements.group(4)
            services_str = elements.group(6)

            # populate the working dictionary
            if gcp_list.has_key(gcp) :
                gcp_list[gcp].update(dict([(itemref , services_str)]))
            else :
                gcp_list[gcp] = dict([(itemref , services_str)])

            # populate the prefixes list
            gs1_prefix = string.join(gcp[0:3][::-1], '.')
            company_code = string.join(gcp[3:8][::-1], '.')
            if prefix_list.has_key(gs1_prefix) :
                if company_code not in prefix_list[gs1_prefix] :
                    prefix_list[gs1_prefix].append(company_code)
            else :
                prefix_list[gs1_prefix] = [ company_code ]

            # ONS levels for GS1 prefixes
            if not ons_levels.has_key(gs1_prefix) :
                ons_levels[gs1_prefix] = elements.group(5)

            count_max = count_max + 1
        else :
            print "Invalid format of URN : %s " % line

    urn_file.close()

    print "Number of products found : %d" % count_max
    count = 0

    # loop for the dictionary of GCPs
    for gcp_item in gcp_list.keys() :

        gs1_prefix = string.join(gcp_item[0:3][::-1], '.')
        company_code = string.join(gcp_item[3:8][::-1], '.')

        current_ons_level = ons_levels[gs1_prefix]


        zone = "%s.%s.%s.id.%s" % (company_code, gs1_prefix, code_type, opt_gen['peer_root'])
        str = 'zone "%s" {\n' % zone 
        str = str + '   type master;\n'
        if current_ons_level == '3' :
            str = str + '   file "%s/db.%s";\n' % (opt_gen['db_path_local'], zone)
        else :
            str = str + '   file "%s/db.%s";\n' % (opt_gen['db_path_dlocal'], zone)
        str = str + '};\n\n'
    
        if current_ons_level == '3' :
            conf_file = open(opt_gen['working_directory'] + '/local-ons/qt-local-ons.conf', 'a')
            conf_file.write(str)
            conf_file.close()
        else :
            conf_file = open(opt_gen['working_directory'] + '/dlocal-ons/qt-dlocal-ons.conf', 'a')
            conf_file.write(str)
            conf_file.close()
            # create delagations in parent zone
            delegation_file = open(opt_gen['working_directory'] + '/root-ons/root-dlocal.db', 'a')
            delegation_file.write('%s.%s.%s.id IN NS %s\n' % (company_code, gs1_prefix, code_type, opt_gen['dlocal_ns']))
            delegation_file.close()
        
        # generate zone file (local ONS)
        if current_ons_level == '3' :
            str = '; Zone file for local-ons (WINGS QTESTS)\n\n'
        else :
            str = '; Zone file for dlocal-ons (WINGS QTESTS)\n\n'
        str = str + '$TTL 1\n\n'
        if current_ons_level == '3' :
            str = str + '@ IN SOA %s %s (\n' % (opt_gen['local_ns'], opt_gen['email'])
        else :
            str = str + '@ IN SOA %s %s (\n' % (opt_gen['dlocal_ns'], opt_gen['email'])
        str = str + '   %s01 ; serial\n' % date.today().strftime("%Y%m%d")
        str = str + '   3h  ; refresh\n'
        str = str + '   1h  ; retry\n'
        str = str + '   1w  ; expire\n'
        str = str + '   1 ) ; negative cache\n\n'

        if current_ons_level == '3' :
            str = str + '   IN NS %s\n\n' % opt_gen['local_ns']
        else :
            str = str + '   IN NS %s\n\n' % opt_gen['dlocal_ns']

        # create naptr records zones for local ons
        for item in gcp_list[gcp_item].keys() :
            product_code = string.join(item[::-1], '.')

            # NAPTR records 
            naptr_elements =  gcp_list[gcp_item][item].split(';<')
            str = str + '\n' + product_code

            for i in range(1, len(naptr_elements)) :
                if i > 1 :
                    str = str + "           "
                str = str + ' naptr %d 0 "u" "%s" "!^.*$!%s!" . ' % ((i-1), naptr_elements[0], naptr_elements[i].rstrip('>')) + "\n" 

            # create data file for queryperf tool
            perf_data_file = open(opt_gen['working_directory'] + '/qperf-data.txt', 'a')
            perf_data_file.write(product_code + "." + zone + " naptr\n")
            perf_data_file.close()

         # add naptr records to zone file (local ONS)
        if current_ons_level == '3' :
            zone_file = open(opt_gen['working_directory'] + '/local-ons/db.' + zone, 'w')
            zone_file.write(str)
            zone_file.close()
        else :
            zone_file = open(opt_gen['working_directory'] + '/dlocal-ons/db.' + zone, 'w')
            zone_file.write(str)
            zone_file.close()

        count = count + 1
        sys.stdout.write("Local zone : %d/%d\r" % (count, len(gcp_list)))
        sys.stdout.flush()


    count = 0
    print

    # loop for the prefixes list
    for prefix in prefix_list.keys() :
        if ons_levels[prefix] != '3' :
            continue

        # create delagations in root zone (for countries)
        delegation_file = open(opt_gen['working_directory'] + '/root-ons/root-country.db', 'a')
        delegation_file.write('%s.%s.id IN NS %s\n' % (prefix, code_type, opt_gen['country_ns']))
        delegation_file.close()

        # create country conf file
        zone = '%s.%s.id.%s' % (prefix, code_type, opt_gen['peer_root'])
        str = 'zone "%s" {\n' % zone 
        str = str + '   type master;\n'
        str = str + '   file "%s/db.%s";\n' % (opt_gen['db_path_country'], zone)
        str = str + '};\n\n'

        conf_file = open(opt_gen['working_directory'] + '/country-ons/qt-country-ons.conf' , 'a')
        conf_file.write(str)
        conf_file.close()
        
        # create the country zone file
        str = '; Zone file for country-ons (WINGS QTESTS)\n\n'
        str = str + '$TTL 1\n\n'
        str = str + '@ IN SOA %s %s (\n' % (opt_gen['country_ns'], opt_gen['email'])
        str = str + '   %s01 ; serial\n' % date.today().strftime("%Y%m%d")
        str = str + '   3h  ; refresh\n'
        str = str + '   1h  ; retry\n'
        str = str + '   1w  ; expire\n'
        str = str + '   1 ) ; negative cache\n\n'
        str = str + '   IN NS %s\n\n' % opt_gen['country_ns']
        str = str + '; Delegations to companies\n\n'

        # delegations to companies for this prefix
        for company_code in prefix_list[prefix] :
            str = str + '%s IN NS %s\n' % (company_code, opt_gen['local_ns'])

        zone_file = open(opt_gen['working_directory'] + '/country-ons/db.' + zone, 'a')
        zone_file.write(str)
        zone_file.close()

        count = count + 1
        sys.stdout.write("Country zone : %d\r" % count)
        sys.stdout.flush()

    print "\nOk."

#
# Usage
#
def usage() :
    print
    print "Provsionning F-ONS WINGS"
    print "Usage : " + sys.argv[0] + "[options] -p <profile>"
    print "  options :"
    print "    -i, --init-dir initialize a working directory"
    print "    -u, --generate EPC URN"
    print "    -z, --generate ONS zones corresponding to existing urn file"
    print "    -p, --profile corresponding profile in the config file"
    print "    -h, --help     show this help"
    print "See config file for other parameters"
    print


#
# Main
#
if __name__ == "__main__":

    # read options from the command line and override previous values 
    if len(sys.argv) == 1 :
        usage()
        sys.exit(2)

    try :
        opts, args = getopt.getopt(sys.argv[1:], "huzip:", ["help", "urn", "zone", "init-dir", "profile"]) 

    except getopt.GetoptError, err:
        print str(err) 
        usage()
        sys.exit(2)

    # main actions
    args = { 'opt_gen_urn' : False, 'opt_gen_zone' : False , 'opt_gen_init_dir' : False , 'opt_profile' : '' }

    for option, value in opts :
        if option in ["-h", "--help"] :
            usage()
            sys.exit(0)
        elif option in ["-u", "--urn"] : 
            args['opt_gen_urn'] = True
        elif option in ["-z", "--zone"] : 
            args['opt_gen_zone'] = True
        elif option in ["-i", "--init-dir"] : 
            args['opt_gen_init_dir'] = True
        elif option in ["-p", "--profile"] : 
            args['opt_profile'] = value.lower() 

    if args['opt_profile'] == '' :
        usage()
        sys.exit(2)

    # read default options in the config file
    conf = ConfigParser.ConfigParser()
    conf.read(os.path.dirname(sys.argv[0]) + "/ons-zone-gen.conf")

    opt_gen={}
    try :
        for option, value in conf.items(args['opt_profile']) :
            opt_gen[option] = value
    except ConfigParser.NoSectionError :
        print "Profile doesn't exist !"
        usage()
        sys.exit(2)

    if args['opt_gen_init_dir'] :
        print "Initialize a working directory..."
        init_dir()
    
    if args['opt_gen_urn'] :
        print "Generate URN list..."
        epc_urn_gen() 

    if args['opt_gen_zone'] :
        print "Generate ONS zones..."
        epc_ons_zone_gen()
