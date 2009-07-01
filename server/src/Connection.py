import stackless
import socket, struct

import Messages

class Connection:
    def __init__(self, clientsocket, address, control):
        # Create a manager channel which can inform us
        # about the results of any external manager's
        # actions (logging in, registering, etc)
        manager = stackless.channel()
        
        # Handle Messages in one tasklet
        stackless.tasklet(self.network)(clientsocket, address)
        # Handle management results in another tasklet
        stackless.tasklet(self.handleManagementMessage)(manager)
        
        self.control = control
        self.manager = manager
        
        self.username = None
        self.character = None
        
        stackless.schedule()
    
    def network(self, clientsocket, address):
        print "Client %s:%s connected..." % (address[0],address[1])
        # For each send we expect the socket returns 1, if its 0 an error ocurred
        if not clientsocket.send('Connection OK\n\rType q! to quit.\n\r> '):
            clientsocket.close()
            return
        data = ''
        while clientsocket.connect:
            data += clientsocket.recv(4096)
            if data == '':
                break
            # If we detect a \n filter the event
            if '\0' in data:
                print data
                
                data = data.rstrip('\0')
                message = struct.unpack('I', data[:2])
                
                if message == Messages.PACKET_LOGIN:
                    # username, password
                    payload = struct.unpack('ss', data[2:])
                elif message == Messages.PACKET_REGISTER:
                    # username, password, email
                    payload = struct.unpack('sss', data[2:])
                elif message == Messages.PACKET_CHAR_MOVE:
                    # x, y
                    payload = struct.unpack('ii', data[2:])
                
                handlePacket(message, payload)
                
                clientsocket.send("> ")
                data = ''
                
            stackless.schedule()
        
        # Loop's over, we broke out for some reason
        # Close the connection
        self.close(clientsocket)
    
    def handlePacket(self, message, payload):
        if self.character:
            # Pass the message onto the PlayerCharacter in a clean form
            if message == Messages.PACKET_CHAR_MOVE:
                self.character.send((Messages.CHAR_MOVE, payload))
                
        elif message == Messages.PACKET_LOGIN:
            username, password = payload
            print "Login: Username: %s, Password: %s" % payload
            
            payload = (username, password, self.manager)
            self.control.send((Messages.CONTROL_LOGIN, payload))
            
        elif message == Messages.PACKET_REGISTER:
            print "Register: Username: %s, Password: %s, Email: %s" % payload
            self.control.send((Messages.CONTROL_REGISTER, payload))

    def close(self, clientsocket):
        clientsocket.close()
        
        # If we are logged in, do some cleanup
        if (self.character):
            self.control.send((Messages.CONTROL_DISCONNECT, self.username))
        
    def handleManagementMessage(self, manager):
        while 1:
            message, payload = manager.receive()
            
            if (message == Messages.MANAGER_LOGGEDIN):
                # Payload is character control channel
                self.username, self.character = payload
                
                # We can now send Messages over the channel
                # Player character will handle them
                print "Got networkChannel for player %s" % self.username
