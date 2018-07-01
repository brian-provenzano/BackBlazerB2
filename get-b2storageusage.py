#!/usr/bin/python3
"""
B2 Backblaze Cloud Total Storage Usage
BJP - 6/25/18
-----------------------
What it does:
>
B2 CLI ( https://www.backblaze.com/b2/docs/quick_command_line.html ) doesnt currently support 
obtaining total b2 cloud storage usage (all buckets) - this fills the gap for me nicely.

I use B2 for personal (free) storage utilizing the 10GB free tier.  This prevents having to 
visit the web interface to get total storage / caps.

Uses my personal B2 library/module BackBlazeB2 (which leverages B2 API)
-----------------------
Usage:
>
get-b2storageusage <accountId> <applicationKey>
-----------------------
Returns:
>
Current BackBlaze B2 Buckets for account:
-----
somebucket [size: 0 (0 B)]
somebucket2 [size: 3381087633 (3.15 GB)]
-----
Total size [3.15 GB]
"""

#--3rd party - see readme for pip install
import requests
from BackBlazeB2 import *

#--std mod/libs
#import base64
import os
import json
import argparse
from enum import Enum


def Main():
    """ Main()"""
    parser = argparse.ArgumentParser(prog="get-b2storageusage", \
            description=" Gets the total size/usage of all objects in b2 account")
    #-required args
    parser.add_argument("accountId", type=str, \
            help="B2 accountId for authorization")
    parser.add_argument("applicationKey", type=str, \
            help="B2 applicationKey for authorization.")
    #- info
    parser.add_argument("-d", "--debug", action="store_true", 
            help="Debug mode - show more informational messages for debugging")
    parser.add_argument("-v", "--version", action="version", version="1.0")
    args = parser.parse_args()
    accountId = args.accountId.strip()
    applicationKey = args.applicationKey.strip()

    try:
        #personal module BackBlazeB2 usage
        b2 = BackBlazeB2(accountId,applicationKey)
        if b2.IsAuthorized:
            buckets = b2.Buckets.All()
            if len(buckets) > 0:
                print("Current BackBlaze B2 Buckets for account [{0}]:".format(accountId))
                print("-----")
                for bucket in buckets:
                    print("{0} [size: {1} ({2})]".format(bucket.name,bucket.size,bucket.sizeHumanReadable))
                print("-----")
                print("Total size [{0}]".format(b2.Buckets.GetUsage(humanReadable=True)))
            else:
                print("No buckets found!")
            
            # print("is there a bucket named 'testbucket'?")
            # b = b2.Buckets.Get("testbucket")
            # if type(b) is B2Bucket:
            #     print("yes, id is :" + b.recId)

        else:
            raise ValueError

    except ValueError as ve:
        Message.Show(MessageType.ERROR, "System ValueError occurred!",str(ve))
    except Exception as e:
        Message.Show(MessageType.ERROR, "UNKNOWN Error Occurred!",str(e))

if __name__ == '__main__':
    Main()