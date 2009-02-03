from pandac.PandaModules import Filename 
import Networking
import sys, os

# Figure out what directory this program is in. 
MYDIR=os.path.abspath(sys.path[0]) 
MYDIR=Filename.fromOsSpecific(MYDIR).getFullpath() + "/../res"

NETWORK=Networking.NetworkConnection()