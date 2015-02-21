#!/usr/bin/python -tt

import sys,getopt
  
import commands
import json
import time
import dateutil.parser
import calendar
 
 
def help():

  print " Usage: launch_config_cleaner.py --filter TEXT-MATCH-AWS-SEARCH [--help] "

 
def main(argv):

  search_filter=None

  # make sure command line arguments are valid
  try:
    options, args = getopt.getopt(

       argv, 
      'hv', 
      [ 
        'help',
        'filter='
    
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
    elif opt in ('', '--filter'):
      search_filter=arg

  if None in [search_filter]:
    help()  	
    sys.exit(2)


  ###################################
  # main code starts here
  ###################################
 
  cmd = """aws autoscaling describe-launch-configurations""" 

  logger.info("Describe launch configurations")

  (status,output) = commands.getstatusoutput(cmd)

  if status>0:
    logger.error("Could not list launch configurations: %s", cmd)
    logger.error(output)
    sys.exit(2)

  #parse the json
  launch_configurations = json.loads(output)

  logger.info("Found %s launch configurations", len(launch_configurations['LaunchConfigurations']) )

  working_set = {}

  for launch_config in launch_configurations['LaunchConfigurations']:

    if search_filter in launch_config['LaunchConfigurationName']:

      dateTime = dateutil.parser.parse(launch_config['CreatedTime'])
      timeStamp = calendar.timegm(dateTime.utctimetuple())
      working_set[ timeStamp ] = launch_config


  logger.info("Found %s launch configurations matching %s", 
  	len(working_set), 
  	search_filter )

  keep_count = 5
  keepers = []

  # lets grab the keepers
  for key in sorted(working_set, reverse=True):

    if len(keepers) < keep_count:
      keepers.append(working_set[key])
      working_set[key] = None

  logger.info("Found %s keepers", 
  	len(keepers) )

 
  # loop over working set delete all old launch configs
  for key in sorted(working_set, reverse=True):

    if working_set[key] != None:

      logger.info("Deleting Launch Configuration: %s " % working_set[key]['LaunchConfigurationName'] )
 
      cmd = """aws autoscaling delete-launch-configuration --launch-configuration-name %s""" % working_set[key]['LaunchConfigurationName']
    
      logger.info("Describe launch configurations")
    
      (status,output) = commands.getstatusoutput(cmd)
    
      if status>0:
        logger.error("Could not delete launch configurations: %s", cmd)
        logger.error(output)
        sys.exit(2)

      logger.info("[OK]")
 

if __name__ == "__main__":
  main(sys.argv[1:])