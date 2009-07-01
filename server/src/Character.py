import stackless
import Messages

class Character:
    def move(self, direction):
        print "moving"

class PlayerCharacter(Character):
    def __init__(self, username, password, email, starter):
        self.username = username
        self.password = password
        self.email = email
        self.starter = starter
        
        self.x = 0
        self.y = 0
    
    def handleNetworkMessage(self, networkChannel):
        while 1:
            # Get the packet
            message, payload = networkChannel.receive()

            if (message == Messages.CHAR_MOVE):
                x, y = payload
                
                print message, payload
            
            stackless.schedule()