class Character:
    def move(self, direction):
        print "moving"

class PlayerCharacter(Character):
    def __init__(self, username, password, email, starter):
        self.username = username
        self.password = password
        self.email = email
        self.starter = starter
    
    def handleNetworkMessage(self, networkChannel):
        while 1:
            # Get the packet
            message = networkChannel.receive()

            print "PlayerChar received packet: %s" % message
            