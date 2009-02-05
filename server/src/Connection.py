import stackless
import socket

import Packets

class Connection:
    def __init__(self, clientsocket, address, control):
        # Create a manager channel which can inform us
        # about the results of any external manager's
        # actions (logging in, registering, etc)
        manager = stackless.channel()
        
        # Handle packets in one tasklet
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
        if not clientsocket.send('Connection OK\n\rType q! to quit.\n\r>'):
            clientsocket.close()
            return
        data = ''
        while clientsocket.connect:
            data += clientsocket.recv(4096)
            if data == '':
                break
            # If we detect a \n filter the event
            if '\n' in data:
                if data == '\r\n':
                    if not clientsocket.send("Unknown command.  Type 'help' to see a list of available commands.\r\n>"):
                        break
                elif data == 'q!\r\n':
                    # If the user sends a q!, close the connection and remove from list
                    print "Closed connection for %s:%s" % (address[0],address[1])
                    #self.control.send("REMOVE", )
                    break
                elif data.startswith('login') & data.endswith('\r\n'):
                    command, username, password = data.rstrip('\r\n').split(' ')
                    print "Command: %s, Username: %s, Password: %s" % (command, username, password)
                    
                    payload = (username, password, self.manager)
                    self.control.send((Packets.CONTROL_LOGIN, payload))
                    
                elif data.startswith('register') & data.endswith('\r\n'):
                    command, username, password, email = data.rstrip('\r\n').split(' ')
                    print "Command: %s, Username: %s, Password: %s, Email: %s" % (command, username, password, email)
                    
                    payload = (username, password, email)
                    self.control.send((Packets.CONTROL_REGISTER, payload))
                    
                elif self.character:
                    # Pass the message onto the PlayerCharacter
                    self.character.send(data.rstrip('\r\n'))
                    
                clientsocket.send(">")
                
                data = ''
            stackless.schedule()
        
        # Loop's over, we broke out for some reason
        # Close the connection
        self.close(clientsocket)
    
    def close(self, clientsocket):
        clientsocket.close()
        
        # If we are logged in, do some cleanup
        if (self.character):
            self.control.send((Packets.CONTROL_DISCONNECT, self.username))
        
    def handleManagementMessage(self, manager):
        while 1:
            message, payload = manager.receive()
            
            if (message == Packets.MANAGER_LOGGEDIN):
                # Payload is character control channel
                self.username, self.character = payload
                
                # We can now send packets over the channel
                # Player character will handle them
                print "Got networkChannel for player %s" % self.username