#!/usr/bin/python -tt

import sys,getopt
 
import logging
import commands
import json
import pprint
import time
import dateutil.parser
import calendar
import re


logger = logging.getLogger('stencil')
hdlr = logging.StreamHandler(sys.stdout)
#hdlr = logging.FileHandler('stencil.log') 
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO) #logging.DEBUG


def help():

  print " Usage: ami_cleaner.py --filter TEXT-TO-MATCH-AWS-SEARCH --regexp \".*BUILD-(\d+)-.*\" [--help] [--live]"
  print "\t Common RegExp: \".*\d{4}-\d{2}-\d{2}-(\d+).*\""

def main(argv):

  search_filter=None
  regexp=None
  live=None
 

  # make sure command line arguments are valid
  try:
    options, args = getopt.getopt(

       argv, 
      'hv', 
      [ 
        'help',
        'verbose',
        'filter=',
        'regexp=',
        'live'
    
      ])
 
  except getopt.GetoptError:
    logging.fatal("Bad options!")
    help()
    sys.exit(2)


  # handle command line arugments
  for opt, arg in options:
    if opt in ('-h', '--help'):
      help()
      sys.exit(2)
    elif opt in ('-v', '--verbose'):
      logger.setLevel(logging.DEBUG) 
    elif opt in ('', '--filter'):
      search_filter=arg
    elif opt in ('', '--regexp'):
      regexp=arg
    elif opt in ('', '--live'):
      live=True

  if None in [search_filter,regexp]:
    help()  	
    sys.exit(2)


  ###################################
  # main code starts here
  ###################################
 
  cmd = """aws ec2 describe-images --owners self""" 
 
  logger.info("Describe AMI's")

  (status,output) = commands.getstatusoutput(cmd)

  if status>0:
    logger.error("Could not list AMI's: %s", cmd)
    logger.error(output)
    sys.exit(2)

  #parse the json
  amis = json.loads(output)

  logger.info("Found %s AMIs", len(amis['Images']) )
 
  working_set = {}

  for ami in amis['Images']:
    if search_filter in ami['Name']:
      # match the build name (get build id)
      pattern = re.compile(regexp)
      match = pattern.match(ami['Name'])
      pprint.pprint(ami['Name'])

      if match: 
        working_set[ int(match.group(1)) ] = ami
       

  logger.info("Found %s AMIs matching %s", 
  	len(working_set), 
  	search_filter )
 
  keep_count = 5
  keepers = []



  # lets grab the keepers
  for key in sorted(working_set, reverse=True):

    if len(keepers) < keep_count:
      keepers.append(working_set[key]) 
      print working_set[key]['Name']
      working_set[key] = None


  logger.info("Found %s keepers", 
  	len(keepers) )
 
  # loop over working set delete all old launch configs
  for key in sorted(working_set, reverse=True):

    if working_set[key] != None:

      logger.info("Deleting AMI: %s image-id %s" % (working_set[key]['Name'],working_set[key]['ImageId'])  )
 
      dryRun = "--dry-run"

      if live:
        dryRun = ""

      cmd = """aws ec2 deregister-image --image-id %s %s""" % (
       working_set[key]['ImageId'],
       dryRun

       )
    
      # (status,output) = commands.getstatusoutput(cmd)
    
      # if status>0:
      #   logger.error("Could not delete AMI: %s", cmd)
      #   logger.error(output)
      #   sys.exit(2)

      # logger.info("[OK]")
 

if __name__ == "__main__":
  main(sys.argv[1:])