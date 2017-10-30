#!/usr/bin/python
import argparse
import sys
import requests
import operator
from os.path import expanduser

class Hue:
  """Class for hue objects
  :param username: Username to be used when connecting to hue bridge
  :param bridge_ip: IP of hue bridge to connect to
  :param light_list: List of lights to take action on
  :param action: Action to take on all lights passed in light_list
  :show_all: If specified no action is taken and status of all lights is shown
  """

  def __init__(self, username, bridge_ip, light_list=None, action=None, show_all=None):
      #set instance vars
      self.username = username
      self.bridge_ip = bridge_ip
      self.bridge_url = "http://" + self.bridge_ip + "/api/" + self.username
      all_lights = self.get_all_lights()
      #print(all_lights.values())

      if show_all == True:
          info_string = ''
          for light_num,light_info in all_lights.items():
              info_string += '%s is ' % light_info['name']
              if light_info['state']['on']:
                info_string += '\x1b[6;30;42m' + 'on' + '\x1b[0m'
              elif not light_info['state']['on']:
                info_string += '\x1b[6;30;41m' + 'off' + '\x1b[0m' + ". "

              info_string += ' and is '
              if light_info['state']['reachable']:
                info_string += '\x1b[6;30;42m' + 'reachable.' + '\x1b[0m\n'
              elif not light_info['state']['reachable']:
                info_string += '\x1b[6;30;41m' + 'unreachable.' + '\x1b[0m\n'
          print(info_string)
          sys.exit()

      elif light_list:
          for light_name in light_list:
              light_num = self.get_light_num(light_name, all_lights)
              if light_num > 0:
                self.set_light(light_num, action)
              else:
                print('Light %s could not be found.  Please ensure your bridge and lights are connected' % light_name)


  def get_all_lights(self):
      lights_url = self.bridge_url + "/lights"
      try:
          response = requests.get(lights_url)
      except:
          sys.exit('Could not find any lights. Please ensure your bridge and lights are connected')

      return response.json()

  def get_light_num(self, light_name, all_lights):
      for light_num,light_info in all_lights.items():
          if light_info['name'] == light_name:
              return light_num
  #def function to fetch status of a light

  #def function to set on attrib of a light
  def set_light(self, light_num, action):
    light_url = self.bridge_url + "/lights/" + light_num + "/state"
    if action == 'on':
      print("set light %s to ON via %s" % (light_num, light_url))
      request = requests.put(light_url, json={"on":True})
    elif action == 'off':
      print("set light %s to OFF via %s" % (light_num, light_url))
      request = requests.put(light_url, json={"on":False})
    print(request.status_code)
  #def function to set brightness of a light

def get_default_username(dot_hue_path):
    #Check if .hue file exists in users home dir.  Read username from the file if it does
    try:
        with open(dot_hue_path, 'r') as f:
            for line in f:
                value = line.split(' ')
                if value[0] == 'username' and len(value[1]) >= 1:
                    return value[1].replace('\n', '')
    except IOError:
        sys.exit("Error: %s could not be read" % dot_hue_path)

    return ''

def get_bridge_ip(hue_nupnp):
    try:
        response = requests.get(hue_nupnp)
        return response.json()[0]['internalipaddress']
    except:
        sys.exit('Could not resolve Hue Bridge IP address. Please ensure your bridge is connected')


#def function to make a hue object

#def main
if __name__ == '__main__':
    #define vars
    HUE_NUPNP = 'https://www.meethue.com/api/nupnp'
    home = expanduser("~")
    dot_hue_path = home + "/.hue"

    #configure arg parser
    parser = argparse.ArgumentParser(description='Control Phillips Hue lights from the CLI')
    parser.add_argument('-u', '--username',help='Username to use when connecting to Hue bridge', default=get_default_username(dot_hue_path), dest='username')
    parser.add_argument('-l', '--light',help='One or more lights to perform an action on', nargs='*', dest='light_list')
    parser.add_argument('-a', '--action', help='Action to perform on lights.  Can be On or Off.', choices=['On', 'on', 'Off', 'off'], dest='action')
    parser.add_argument('-s', '--show_all', help='Show all lights and their status', action='store_true', dest='show_all')
    args = parser.parse_args()

    #make sure either cmd line arg or reading from .hue file gave us a username
    if len(args.username) == 0:
        sys.exit("Error: Username must be provided as argument or in %s" % dot_hue_path)

    bridge_ip = get_bridge_ip(HUE_NUPNP)

    #print('Username is %s and bridge IP is %s' % (args.username, bridge_ip))
    #print('lights to perform action %s on are %s' % (args.action, args.light_list))
    if args.show_all == True:
        Hue(args.username, bridge_ip, show_all=True)
    elif (args.light_list and not args.action) or (args.action and not args.light_list):
        sys.exit("Both -l and -a must specified in order to take action on a light")
    elif args.light_list and args.action:
        Hue(args.username, bridge_ip, light_list=args.light_list, action=args.action.lower())
