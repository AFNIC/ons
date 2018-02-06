#!/bin/bash 

UPDATE_SERIAL_SCRIPT=/etc/ons/scripts/update_zone_serial/update_zone_serial.sh
ONSCTL_SCRIPT=/etc/ons/scripts/rc.d/onsctl
DB_PROD_ROOT_ONS=/var/ons/prod-platform/root-ons
DB_PROD_COUNTRY_ONS=/var/ons/prod-platform/country-ons
DB_PROD_LOCAL_ONS=/var/ons/prod-platform/local-ons
DB_PROD_DLOCAL_ONS=/var/ons/prod-platform/dlocal-ons
WORKING_DIRECTORY=./work

#
# Clean the current working directory
#
reset_working_directory() {
    rm -rf $WORKING_DIRECTORY.old
    if [ -d $WORKING_DIRECTORY ]
    then 
        mv $WORKING_DIRECTORY $WORKING_DIRECTORY.old
    fi
    mkdir $WORKING_DIRECTORY
    mkdir $WORKING_DIRECTORY/root-ons
    mkdir $WORKING_DIRECTORY/country-ons
    mkdir $WORKING_DIRECTORY/local-ons
    mkdir $WORKING_DIRECTORY/dlocal-ons
}


#
# Update zone serials (with a dedicated script)
#
update_zone_serial() {
    $UPDATE_SERIAL_SCRIPT $DB_PROD_ROOT_ONS/db.wings-root-ons
    $UPDATE_SERIAL_SCRIPT $DB_PROD_COUNTRY_ONS/db.wings-country-ons
    $UPDATE_SERIAL_SCRIPT $DB_PROD_LOCAL_ONS/db.wings-local-ons
    $UPDATE_SERIAL_SCRIPT $DB_PROD_DLOCAL_ONS/db.wings-dlocal-ons

    # restart F-ONS system
    $ONSCTL_SCRIPT restart
}


#
# Clean the name server : remove all files and update the zone serials
#
reset_production_directory() {
    rm -f $DB_PROD_ROOT_ONS/quantitative_tests/*
    touch $DB_PROD_ROOT_ONS/quantitative_tests/root-country.db
    touch $DB_PROD_ROOT_ONS/quantitative_tests/root-dlocal.db

    rm -f $DB_PROD_COUNTRY_ONS/quantitative_tests/*
    touch $DB_PROD_COUNTRY_ONS/quantitative_tests/qt-country-ons.conf

    rm -f $DB_PROD_LOCAL_ONS/quantitative_tests/*
    touch $DB_PROD_LOCAL_ONS/quantitative_tests/qt-local-ons.conf

    rm -f $DB_PROD_DLOCAL_ONS/quantitative_tests/*
    touch $DB_PROD_DLOCAL_ONS/quantitative_tests/qt-dlocal-ons.conf

    # update the zone serials
    update_zone_serial
}


#
# Copy all generated files on the name server and update the zone serials
#
push_production_files() {
    # copy new zone and config files
    cp -f $WORKING_DIRECTORY/root-ons/* $DB_PROD_ROOT_ONS/quantitative_tests/
    cp -f $WORKING_DIRECTORY/country-ons/* $DB_PROD_COUNTRY_ONS/quantitative_tests/
    cp -f $WORKING_DIRECTORY/local-ons/* $DB_PROD_LOCAL_ONS/quantitative_tests/
    cp -f $WORKING_DIRECTORY/dlocal-ons/* $DB_PROD_DLOCAL_ONS/quantitative_tests/

    # update the zone serials
    update_zone_serial
}

#
# Main
#

if [ "$2" != "" ]
then
    WORKING_DIRECTORY=$2
fi

case "$1" in
    reset-wd ) 
        reset_working_directory 
        ;;
    reset-prod )
        reset_production_directory 
        ;;
    push-prod ) 
        push_production_files
        ;;
    update-serials )
        update_zone_serial
        ;;
    * ) 
    echo "Usage :"
    echo "$0 [reset-wd|reset-prod|push-prod|update-serials] [directory]"
        ;;
esac

exit 0
