import sys, time
import stackless

import StacklessSocket
#sys.modules["socket"] = stacklesssocket
StacklessSocket.install()
import socket

import Connection
import UserManager

class Server(object):
    def __init__(self, conn):
        # Create an INET, STREAMing socket
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to an addres, and a port
        self.serversocket.bind(conn)
        # Become a server socket
        self.serversocket.listen(5)
        
        control = stackless.channel()
        
        stackless.tasklet(self.acceptConnection)(control)
        
        UserManager.UserManager(control)

    def acceptConnection(self, control):
        while self.serversocket.accept:
            # Accept connections from outside
            (clientsocket, address) = self.serversocket.accept()
            
            # Now do something with the clientsocket
            # In this case, each client is managed in a tasklet
            
            # Also activate the connection handler
            Connection.Connection(clientsocket, address, control)
            # We don't track the clients until they are logged in now.
            #self.clients[clientsocket] = (address, Connection.Connection(clientsocket, address))
            

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 7566
    print "Starting up server on IP:port %s:%s" % (host, port)
    s = Server((host,port))
    stackless.run()