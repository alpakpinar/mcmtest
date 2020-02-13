#!/bin/bash

# Set the VOMS proxy
export X509_USER_PROXY=${1}
voms-proxy-info -all
voms-proxy-info -all -file ${1}

PREPID=${2}

# Clean any previous HIG files
rm "HIG*" 2>/dev/null
OUTFILE="test_com_${PREPID}"

wget --no-check-certificate -O ${OUTFILE} "https://cms-pdmv.cern.ch/mcm/public/restapi/requests/get_test/${PREPID}"

echo "Running test job: ${PREPID}"
bash ${OUTFILE}
