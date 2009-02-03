import stackless

import Character

class UserManager(object):
    def __init__(self, control):
        # FIXME: registered user DB
        self.userDB = {}
        
        # Logged in user list
        self.users = {}
        
        # We have a special control channel through which user management occurs
        stackless.tasklet(self.handleControlMessage)(control)
    
    def handleControlMessage(self, control):
        while 1:
            # Message and payload
            message, payload = control.receive()
        
            if (message == "LOGIN"):
                # payload is username and password
                # manager is used to send back the login result
                username, password, manager = payload
            
                # make sure we're not logged in already and then do basic existence check
                if (not self.users.get(username, 0) and self.userDB.get(username, 0)):
                    # this is the authenticator/password check
                    if (self.userDB[username].password == password):
                        print "Authentication successful"
                        character = self.userDB[username]
                        
                        # We are in!
                        self.users[username] = character
                        
                        # Create a channel and tasklet which can handle networking
                        # for this guy (i.e. allow the connection tasklet to delegate
                        # most packets to the character's networking tasklet)
                        characterChannel = stackless.channel()
                        stackless.tasklet(character.handleNetworkMessage)(characterChannel)
                        
                        # Give the Connection access to the network channel
                        # so it can pass on packets to the PlayerCharacter.
                        manager.send(("LOGGEDIN", (username, characterChannel)))
                        
                        print "Logged in"
                    else:
                        print "Failed password check"
                else:
                    print "Failed existence check"
                    
            elif (message == "REGISTER"):
                # payload is triple of registration data
                username, password, email = payload
                self.userDB[username] = Character.PlayerCharacter(username, password, email, 0)
                print "Registered"
            
            elif (message == "DISCONNECT"):
                # Payload is username of the disconnected
                # Just delete them from the logged in list
                self.users[payload] = None
                
                print "Logged out %s" % payload