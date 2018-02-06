#!/usr/bin/env python

####
# Library for testing Federated ONS : from EPC code to URL 
# URI format : urn:epc:id:sgtin:CompanyPrefix.ItemReference.SerialNumber
# AFNIC R&D 2010
####

import dns.resolver
import string
import re
from dns.exception import DNSException
import os
import sys
import getpass

##
# Convert EPC hex value to URI
##
def hex_to_bin(d, nb = 0):
    conv = {
        '0' : '0000', '1' : '0001', '2' : '0010', '3' : '0011', '4' : '0100',
        '5' : '0101', '6' : '0110', '7' : '0111', '8' : '1000', '9' : '1001',
        'A' : '1010', 'B' : '1011', 'C' : '1100', 'D' : '1101', 'E' : '1110', 'F' : '1111'
    }
    return "".join([conv[ch] for ch in d]).zfill(nb)

def binstr_to_decimal(x):
    return sum(map(lambda z: int(x[z]) and 2**(len(x) - z - 1), range(len(x)-1, -1, -1)))

def hexepc_to_uri(hexepc) :
    binepc = hex_to_bin(hexepc)
    header = binepc[:8]
    filter = binepc[8:11]
    partition = binepc[11:14]
    num_bits_comp = 0
    num_bits_item = 0

    if (partition == '100'):
        num_bits_comp = 27
        num_bits_item = 17
    elif (partition == '101'):
        num_bits_comp = 24
        num_bits_item = 20

    end_comp_prefix = num_bits_comp + 14
    end_item_ref    = end_comp_prefix + num_bits_item

    comp_prefix = binepc[14:end_comp_prefix]
    item_ref    = binepc[end_comp_prefix:end_item_ref]

    comp_prefix = binstr_to_decimal(comp_prefix)
    item_ref = binstr_to_decimal(item_ref)

    # Creating the URI
    if (partition == '100'):
        return 'urn:epc:id:sgtin:''%08d' % comp_prefix + '.' + '%05d' % item_ref
    elif(partition == '101'):
        return 'urn:epc:id:sgtin:''%07d' % comp_prefix + '.' + '%06d' % item_ref
    else :
        return ''

##
# Supported GS1 codes
##
def is_gtin13(code) :
    if re.search(re.compile("^[0-9]{13}$"), code) :
        return True
    else :
        return False

def is_epc96_hex(code) :
    if re.search(re.compile("^[A-F0-9]{24}$"), code.upper()) :
        return True
    else :
        return False

def is_epc96_urn(code) :
    elements = re.search(re.compile("^urn:epc:id:sgtin:([0-9]+)\.([0-9]+)(\.[0-9]+)?$"), code.lower())
    if elements :
        if len(elements.group(1)) + len(elements.group(2)) == 13 :
            return True
    return False

##
# Convert barcode to URI
##
def barcode_to_fqdn(barcode, domain_name) :
    fqdn = string.join(barcode, '.')[::-1] # invert and explode string with "."
    fqdn += '.gtin.id.' + domain_name 
    return fqdn

##
# Build FQDN based on epc code and root domain name
##
def uri_to_fqdn(uri, domain_name) :
    elements = re.search(re.compile("^urn:epc:([a-z]+):([a-z]+):([0-9]+)\.([0-9]+)(\.[0-9]+)?$"), uri.lower())

    if elements :
        fqdn = ""
        fqdn = string.join(elements.group(4)[::-1], '.') # reverse and add ItemReference
        fqdn += '.' + string.join(elements.group(3)[::-1], '.') # reverse and add CompanyPrefix
        fqdn += '.' + elements.group(2) # add type (ex 'sgtin')
        fqdn += '.' + elements.group(1) # add id class (ex 'id')
        fqdn += '.' + domain_name # add ONS root domain name
        return fqdn 

    return ""

##
# Evaluate NAPTR response
##
def naptr(fqdn, service_type, name_server):
    try:
        # request the ONS recursive name server
        naptr = dns.message.make_query(fqdn, dns.rdatatype.from_text('NAPTR'))
        msg = dns.query.udp(naptr, name_server) 

        # test returned code
        if msg.rcode() != dns.rcode.NOERROR :
            raise DNSException(dns.rcode._by_value[msg.rcode()])

        # show the result of the query
        for rr_set in msg.answer :
            # detect any redirection by DNAME (generate a CNAME - switch to another ONS root)
            if rr_set.rdtype == dns.rdatatype.CNAME :
                (str1, sep, str2) = rr_set.to_text().partition('CNAME ')
                print_info("=> FQDN modification (redirection occurred): " + str2)

            # NAPTR response
            if rr_set.rdtype == dns.rdatatype.NAPTR :
                
                selected_answers = []
                
                # filter : keep only desired service and valid flags
                for rdata in rr_set :
                    # print rdata
                    if ((rdata.order == 1) and
                        ((service_type.lower() == rdata.service.lower() and rdata.flags == 'u') 
                        or (rdata.service.lower() == "" and rdata.flags == ""))):
                        selected_answers.append(rdata)
                    
                # select the best answser (NAPTR algorithm)
                if len(selected_answers) >= 1:
                    selected_answers.sort(lambda x,y: cmp(x.preference, y.preference)) # order by preference
                    rdata = selected_answers[0] # take only the first item (lower preference)
                    print_info("=> ONS response: NAPTR " + rdata.to_text())
            	    elements = re.match(re.compile("!(.*)!(.*)!"), rdata.regexp) # retrive url rewriting 
                    return (rdata.flags, elements.group(1), elements.group(2)) 
                else:
                    print "==> No appropriate service found for this product ! \n"
                    return (None, "", "") 

    except DNSException, e :
        # print "*** ONS report : ", e.__class__, e
        print e.__class__, e
        print
        return (None, "", "") 

##
# NAPTR answer
##
def code2url(code, domain_name, name_server, service_type):

    fqdn = ""

    if name_server == "" :
        # use default name servers (resolv.conf)
        name_server = dns.resolver.Resolver().nameservers[0]

    print "Configuration : service=" + service_type + ", nameserver=" + name_server + ", ONS Root=" + domain_name

    if is_gtin13(code) :
        print_info("\n> Barcode: " + code) # Barcode -GTIN-13
        fqdn = barcode_to_fqdn(code, domain_name) # Barcode -GTIN-13
    
    elif is_epc96_urn(code) :
        print_info("\n> URI EPC: " + code) # URN EPC

        # convert URI into FQDN
        fqdn = uri_to_fqdn(code, domain_name)

    elif is_epc96_hex(code) :
        print_info("\n> EPC: 0x" + code) # EPC 96 bits

        # convert EPC to URI
        uri = hexepc_to_uri(code) # EPC 96 bits
        print_info("=> URI translation: " + uri)

        # convert URI into FQDN
        fqdn = uri_to_fqdn(uri, domain_name)
    else :
        print_info("Invalid code : " + code)
        return ""

    print_info("=> FQDN translation : " + fqdn + ".")

    if len(fqdn) == 0 :
        return ""

    # NAPTR response
    (ret, regexp, result_uri) = naptr(fqdn, service_type, name_server)
    
    if ret == '': # NAPTR rewrite rule
        fqdn = uri_to_fqdn(uri, regexp, result_uri)
        print_info("=> Rewriting FQDN (redirection occurred): " + fqdn)
        (ret, regexp, result_uri) = naptr(fqdn, service_type, name_server)

    if ret == 'u': # terminal rule - return the final url
        if regexp == "^.*$" :
            print_info("=> Service proposed for that product class: " + result_uri)
            return result_uri
    
    else :
        return ""

##
# Print info 
##
def print_info(outstr):
    print outstr
    print

##
# End
##
