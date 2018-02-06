#!/usr/bin/env python

####
# Python Library for convert EPC in several format
# Input/Ouput string can be EPC SGTIN-96 URN, EPC hexa value
# Parition (101), Filter(001) and Header Value (0011 0000) are hardcoded
# Before any modification, please refer to the GS1 reference "EPC Tag Data Standard"
# AFNIC R&D 2011
####

import os, sys, string, re

##
# String operations
##

# String operation : binary to decimal
def str_bin2int(bin_str) :
    return int(bin_str, 2)

# String operation : hexa to binary string
def str_hex2bin(hexa_str) :

    hex_bin = {
        "0":"0000", "1":"0001", "2":"0010", "3":"0011", "4":"0100", 
        "5":"0101", "6":"0110", "7":"0111", "8":"1000", "9":"1001", 
        "A":"1010", "B":"1011", "C":"1100", "D":"1101", "E":"1110", "F":"1111" }

    return "".join([hex_bin[char] for char in hexa_str])

# String operation : int to binary string
def str_int2bin(int_n):
    bin_str = ''
    if int_n < 0: raise ValueError, "must be a positive integer"
    if int_n == 0: return '0'
    while int_n > 0:
        bin_str = str(int_n % 2) + bin_str
        int_n = int_n >> 1
    return bin_str

# String operation : binary to hexa string
def str_bin2hexa(bin_str):
    bin_hex = {
            "0000":"0", "0001":"1", "0010":"2", "0011":"3", "0100":"4", 
            "0101":"5", "0110":"6", "0111":"7", "1000":"8", "1001":"9", 
            "1010":"A", "1011":"B", "1100":"C", "1101":"D", "1110":"E", "1111":"F" }

    start = 0
    end   = 4
    i     = 0
    hex_str = ''
    while (i < 24):
        hex = bin_str[start:end]
        while ((len(hex)) < 4) :
            hex = hex + '0'
        character = bin_hex[hex]
        hex_str += character
        start = start + 4
        end   = end + 4
        i     = i + 1 
    return hex_str


##
# Convert EPC from Hexa format to URN Pure Identity format 
##
def epc_hexa2urn(hexa_str) :

    bin_str = str_hex2bin(hexa_str)

    header     = bin_str[:8]
    filter     = bin_str[8:11]
    partition  = bin_str[11:14]
    gcp_length = 0
    itemref_length = 0

    if(partition == '100'): 
        gcp_length = 27
        itemref_length = 17
    elif(partition == '101'):
        gcp_length = 24
        itemref_length = 20
    
    gcp_end_index = gcp_length + 14
    itemref_end_index = gcp_end_index + itemref_length

    gcp = bin_str[14:gcp_end_index]
    itemref = bin_str[gcp_end_index:itemref_end_index]
    serialnum = bin_str[itemref_end_index::]    

    #print 'Header: ', header
    #print 'Filter: ', filter
    #print 'Partition: ', partition
    #print 'Binary gcp: ', gcp
    #print 'Binary item reference: ', itemref
    #print 'Serial number: ', serialnum 
 
    gcp = str_bin2int(gcp)
    itemref = str_bin2int(itemref)
    serialnum = str_bin2int(serialnum)

    # Creating the final URN 
    urn = "urn:epc:id:sgtin:"
    if(partition == '100'):
        urn = urn + '%08d' % gcp + '.' + '%05d' % itemref
    elif(partition == '101'):
        urn = urn + '%07d' % gcp + '.' + '%06d' % itemref
    
    if serialnum != "" :
        urn = urn + "." + str(serialnum)

    return urn


##
# Convert EPC from URN Pure Identity format to Hexa format
##
def epc_urn2hexa(urn) :

    gcp = ""
    itemref = ""
    serialnum = ""

    header = "00110000"
    filter = "001"
    partition = "101"
    initval = header + filter + partition 

    elements = re.search(re.compile("^urn:epc:id:sgtin:([0-9]+)\.([0-9]+)(\.[0-9]+)?$"), urn.lower())
    if elements :
        if len(elements.group(1)) + len(elements.group(2)) == 13 :
            gcp = elements.group(1)
            itemref = elements.group(2)
        if elements.group(3) :
            serialnum = elements.group(3)[1:]
    else :
        print "Not a valid EPC SGTIN-96 URN ! "
        sys.exit(2)
    
    gcp = str_int2bin(int(gcp))
    itemref = str_int2bin(int(itemref))
    if len(serialnum) > 0 :
        serialnum  = str_int2bin(int(serialnum))
        serialnum = serialnum.zfill(38)

    if(partition == '100'):
        print '%027d' % gcp 
        print '%017d' % itemref
    elif(partition == '101'):
        gcp = gcp.zfill(24)
        itemref = itemref.zfill(20)
    
    bin_val = initval + gcp + itemref + serialnum
    # print "Binary value : " + bin_val + " (" + str(len(bin_val)) + " bits )"

    return str_bin2hexa(bin_val)
