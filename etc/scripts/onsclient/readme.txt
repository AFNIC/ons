F-ONS Client

* Library

This short library is used in the app client and web client. The aim is to have a 
functional implementation of NAPTR operations for ONS (see RFC in the references section).

* Main functions :

    * EPC translation :
          o hexepc_to_uri(n) : hexa to EPCglocbal Standard URI 
    * Translation to FQDN :
          o uri_to_fqdn(uri, regexp, rewrite) : from EPC URI to fully qualified domain name
          o barcode_to_fqdn(barcode, domain_name) : from GTIN to fully qualified domain name 
    * NAPTR operations :
          o naptr(fqdn, service, name_server) : make the DNS request and get the final result (URL)
          o code2url(code, ons_resolv_conf, service) :main function, input is a GS1 
    * Resolver configuration :
          o get_ons_resolv_conf(resolv_file) : get default ONS resolver and default domain name (ONS root) 


* Standalone Client

The demo ONS client (based on previous library) is used to query the F-ONS, with :

    * EPC from our RFID reader (UDL5)
    * GTIN (barcode) from our barcode reader
    * EPC or GTIN from command line 


The synopsis is : 
Usage : ./onsclient-demo.py [options] [-c GS1-CODE] -r ONSROOT
options :
    -h, --help          show this help
    -q, --quiet         quiet mode, no output
    -s, --step          output step by step
    -f, --rfid          enable RFID/EPC reading from log file
    -b, --browser       open final url in default web browser
    -c, --code          EPC (24 hexa) or barcode (GTIN-13)
    -r, --root          ONS root queried by default : [onseu|onsas|onsam|ons-peer-eu|ons-peer-com|ons-peer-asia|onsepc1]

Examples :
./onsclient-demo.py -c 3074B77F2861B34000000954 -p ons-peer-eu

> RFID/EPC: 0x3074B77F2861B34000000954

=> URI translation: urn:epc:id:sgtin:3006410.100045

==> FQDN translation (ONS-ROOT='ons-peer.eu'): 5.4.0.0.0.1.0.1.4.6.0.0.3.sgtin.id.ons-peer.eu.

===> ONS response: NAPTR 0 0 "u" "EPC+html" "!^.*$!http://www.friskpowermint.ch/fr/product/peppermint.html!" .

====> Service proposed for that product class: http://www.friskpowermint.ch/fr/product/peppermint.html

Important : the ONS (DNS) resolver is set in the resolv_conf directory (in this case in the ons-peer-eu.conf file.


* References
    o RFC3401 : Dynamic Delegation Discovery System (DDDS) - Part One: The Comprehensive DDDS
    o RFC3402 : Dynamic Delegation Discovery System (DDDS) - Part Two: The Algorithm
    o RFC3403 : Dynamic Delegation Discovery System (DDDS) - Part Three: The Domain Name System (DNS) Database
    o RFC3404 : Dynamic Delegation Discovery System (DDDS) - Part Four: The Uniform Resource Identifiers (URI) Resolution Application
    o RFC3761 : The E.164 to Uniform Resource Identifiers (URI) - Dynamic Delegation Discovery System (DDDS) Application (ENUM) 
