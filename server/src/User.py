import Connection
import stackless

class User:
    def __init__(self, connection):
        self.connection = connection

        # The tasklet will hold a reference to the user keeping the instance
        # alive as long as it is handling commands.
        stackless.tasklet(self.run)()

    def run(self):
        global server

        # Notify the server that a user is connected.
        server.registerUser(self)
        logging.info("Connected %d from %s", id(self), self.connection.clientAddress)

        try:
            while self.handleCommand():
                pass

            self.onUserDisconnection()
        except Connection.RemoteDisconnectionError:
            self.onRemoteDisconnection()
            self.connection = None
        except:
            traceback.print_exc()
        finally:
            if self.connection:
                self.connection.disconnect()
                self.connection = None

    def handleCommand(self):
        self.connection.write("> ")
        line = self.connection.readLine()
        words = [ word.strip() for word in line.strip().split(" ") ]
        verb = words[0]

        if verb == "look":
            userList = server.listUsers()
            self.connection.writeLine("There are %d users connected:" % len(userList))
            self.connection.writeLine("Name\tHost\t\tPort")
            self.connection.writeLine("-" * 40)
            for user in userList:
                host, port = user.connection.clientAddress
                self.connection.writeLine("Unknown\t"+ str(host) +"\t"+ str(port))
        elif verb == "say":
            line = line[4:]
            secondPartyPrefix = "Someone says: "
            for user in server.listUsers():
                if user is self:
                    prefix = "You say: "
                else:
                    prefix = secondPartyPrefix
                user.connection.writeLine(prefix + "\"%s\"" % line)
        elif verb == "quit":
            return False
        elif verb == "help":
            self.connection.writeLine("Commands:")
            for verb in [ "look", "say", "quit", "help" ]:
                self.connection.writeLine("  "+ verb)
        else:
            self.connection.writeLine("Unknown command.  Type 'help' to see a list of available commands.")

        return True

    def onRemoteDisconnection(self):
        logging.info("Disconnected %d (remote)", id(self))

    def onUserDisconnection(self):
        logging.info("Disconnected %d (local)", id(self))