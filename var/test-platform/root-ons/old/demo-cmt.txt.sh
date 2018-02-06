#!/bin/bash

# script utilisé pour la demo avec code 2D :
#  - switch entre : CMT sans Malta par defaut <-> CMT avec Malta
#  - un paramètre obligatoire (on|off)

function usage() {
    echo "$0 [on|off]"
}

OPT=$1

if [ "$OPT" != "on1" -a "$OPT" != "on2" -a "$OPT" != "off" ]
then
    usage
    exit 0
fi

cd /var/www/cmt/
ref_link="cmt.txt"
switch_default_file="cmt.txt.default"
switch_demo_file1="cmt.txt.demo1"
switch_demo_file2="cmt.txt.demo2"

if [ "$OPT" == "on1" ]
then
    if [ -f $switch_demo_file1 ]
    then
        rm $ref_link
        ln -s $switch_demo_file1 $ref_link
    fi
elif [ "$OPT" == "on2" ]
then
    if [ -f $switch_demo_file2 ]
    then
        rm $ref_link
        ln -s $switch_demo_file2 $ref_link
    fi
elif [ "$OPT" == "off" ]
then
    if [ -f $switch_default_file ]
    then
        rm $ref_link
        ln -s $switch_default_file $ref_link
    fi
fi
