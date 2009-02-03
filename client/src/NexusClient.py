"""Roamers is a simple demo consisting of: 

   * A 3D environment 
   * A keyboard-controlled animated player character (class Character) 
   * A 3rd-person camera that follows the player (class Camera) 
   * And some non-player characters with their own animated avatars
     (class Agent) 

   The main class that initialises everything is the Game class. 
    
   Roamers is based on Panda3D's Tut-Roaming-Ralph.py by Ryan Myers and uses 
   models and animations from Panda3D's collection. 
    
   Classes: 
   Camera -- A 3rd-person floating camera that follows an actor around. 
   Character -- An animated, 3D character that moves in response to control 
                settings. These control settings can be used by a deriving 
                class to create non-playe character behaviours (as in class 
                Agent_ or can be hooked up to keyboard keys to create a 
                player character (see Game.__init__()). 
   Agent -- A computer-controlled extension of Character. 
   Game -- The game world: environment, characters, camera, onscreen text and 
           keyboard controls. 
   """ 

import direct.directbase.DirectStart 
from Character import Character
import Config
from pandac.PandaModules import CollisionTraverser,CollisionNode 
from pandac.PandaModules import CollisionHandlerQueue,CollisionRay 
from pandac.PandaModules import Filename 
from pandac.PandaModules import PandaNode,NodePath,Camera,TextNode 
from pandac.PandaModules import Vec3,Vec4,BitMask32 
from direct.gui.OnscreenText import OnscreenText 
from direct.gui.DirectGui import *
from direct.actor.Actor import Actor 
from direct.task.Task import Task 
from direct.showbase.DirectObject import DirectObject 
import random, sys, os, math 


class Camera: 
    
    """A floating 3rd person camera that follows an actor around, and can be 
    turned left or right around the actor. 

    Public fields: 
    self.controlMap -- The camera's movement controls. 
    actor -- The Actor object that the camera will follow. 
    
    Public functions: 
    init(actor) -- Initialise the camera. 
    move(task) -- Move the camera each frame, following the assigned actor. 
                  This task is called every frame to update the camera. 
    setControl -- Set the camera's turn left or turn right control on or off. 
    
    """ 

    def __init__(self,actor): 
        """Initialise the camera, setting it to follow 'actor'. 
        
        Arguments: 
        actor -- The Actor that the camera will initially follow. 
        
        """ 
        
        self.actor = actor 
        self.prevtime = 0 

        # The camera's controls: 
        # "left" = move the camera left, 0 = off, 1 = on 
        # "right" = move the camera right, 0 = off, 1 = on 
        self.controlMap = {"left":0, "right":0} 

        taskMgr.add(self.move,"cameraMoveTask") 

        # Create a "floater" object. It is used to orient the camera above the 
        # target actor's head. 
        
        self.floater = NodePath(PandaNode("floater")) 
        self.floater.reparentTo(render)        

        # Set up the camera. 

        base.disableMouse() 
        base.camera.setPos(self.actor.getX(),self.actor.getY()+2, 2)
        # uncomment for topdown
        #base.camera.setPos(self.actor.getX(),self.actor.getY()+10,2) 
        #base.camera.setHpr(180, -50, 0)
        
        # A CollisionRay beginning above the camera and going down toward the 
        # ground is used to detect camera collisions and the height of the 
        # camera above the ground. A ray may hit the terrain, or it may hit a 
        # rock or a tree.  If it hits the terrain, we detect the camera's 
        # height.  If it hits anything else, the camera is in an illegal 
        # position. 

        self.cTrav = CollisionTraverser() 
        self.groundRay = CollisionRay() 
        self.groundRay.setOrigin(0,0,1000) 
        self.groundRay.setDirection(0,0,-1) 
        self.groundCol = CollisionNode('camRay') 
        self.groundCol.addSolid(self.groundRay) 
        self.groundCol.setFromCollideMask(BitMask32.bit(1)) 
        self.groundCol.setIntoCollideMask(BitMask32.allOff()) 
        self.groundColNp = base.camera.attachNewNode(self.groundCol) 
        self.groundHandler = CollisionHandlerQueue() 
        self.cTrav.addCollider(self.groundColNp, self.groundHandler) 

        # Uncomment this line to see the collision rays 
        #self.groundColNp.show() 
      
    def move(self,task): 
        """Update the camera's position before rendering the next frame. 
        
        This is a task function and is called each frame by Panda3D. The 
        camera follows self.actor, and tries to remain above the actor and 
        above the ground (whichever is highest) while looking at a point 
        slightly above the actor's head. 
        
        Arguments: 
        task -- A direct.task.Task object passed to this function by Panda3D. 
        
        Return: 
        Task.cont -- To tell Panda3D to call this task function again next 
                     frame. 
        
        """ 

        # FIXME: There is a bug with the camera -- if the actor runs up a 
        # hill and then down again, the camera's Z position follows the actor 
        # up the hill but does not come down again when the actor goes down 
        # the hill. 

        elapsed = task.time - self.prevtime 

        # If the camera-left key is pressed, move camera left. 
        # If the camera-right key is pressed, move camera right. 
        
        # comment out for topdown  
        base.camera.lookAt(self.actor) 
        
        camright = base.camera.getNetTransform().getMat().getRow3(0) 
        camright.normalize() 
        if (self.controlMap["left"]!=0): 
            base.camera.setPos(base.camera.getPos() - camright*(elapsed*20)) 
        if (self.controlMap["right"]!=0): 
            base.camera.setPos(base.camera.getPos() + camright*(elapsed*20)) 

        # If the camera is too far from the actor, move it closer. 
        # If the camera is too close to the actor, move it farther.

        camvec = self.actor.getPos() - base.camera.getPos() 
        camvec.setZ(0) 
        camdist = camvec.length() 
        camvec.normalize() 
        if (camdist > 10.0): 
            base.camera.setPos(base.camera.getPos() + camvec*(camdist-10)) 
            camdist = 10.0 
        if (camdist < 5.0): 
            base.camera.setPos(base.camera.getPos() - camvec*(5-camdist)) 
            camdist = 5.0 

        # Now check for collisions. 

        self.cTrav.traverse(render) 

        # Keep the camera at one foot above the terrain, 
        # or two feet above the actor, whichever is greater. 
        # comment out for topdown
        
        entries = [] 
        for i in range(self.groundHandler.getNumEntries()): 
            entry = self.groundHandler.getEntry(i) 
            entries.append(entry) 
        entries.sort(lambda x,y: cmp(y.getSurfacePoint(render).getZ(), 
                                     x.getSurfacePoint(render).getZ())) 
        if (len(entries)>0) and (entries[0].getIntoNode().getName() == "terrain"): 
            base.camera.setZ(entries[0].getSurfacePoint(render).getZ()+1.0) 
        if (base.camera.getZ() < self.actor.getZ() + 2.0): 
            base.camera.setZ(self.actor.getZ() + 2.0) 
            
        # The camera should look in the player's direction, 
        # but it should also try to stay horizontal, so look at 
        # a floater which hovers above the player's head. 
        
        self.floater.setPos(self.actor.getPos()) 
        self.floater.setZ(self.actor.getZ() + 2.0)
        
        #self.floater.setZ(self.actor.getZ() + 10.0) 
        #self.floater.setY(self.actor.getY() + 7.0)
        
        # comment out for topdown
        base.camera.lookAt(self.floater) 
        
        base.camera.setPos(self.floater.getPos())
        
        # Store the task time and continue. 
        self.prevtime = task.time 
        return Task.cont 

    def setControl(self, control, value): 
        """Set the state of one of the camera's movement controls. 
        
        Arguments: 
        See self.controlMap in __init__. 
        control -- The control to be set, must be a string matching one of 
                   the strings in self.controlMap. 
        value -- The value to set the control to. 
        
        """ 

        # FIXME: this function is duplicated in Camera and Character, and 
        # keyboard control settings are spread throughout the code. Maybe 
        # add a Controllable class? 
        
        self.controlMap[control] = value 

class Agent(Character, DirectObject): 
    """A computer-controlled non-player character. 
    
    This class derives from Character. 
    
    New public fields: 
    None. 
    
    New public functions: 
    None. 
    
    Functions extended from Character: 
    __init__ -- Initialise some private fields. 
    move -- Make the character run around randomly. 
    
    """ 
    
    def __init__(self,model,run,walk,startPoint,scale): 
        """Initialise the character. 
        
        Initialises private fields used to control the character's behaviour. 
        Also see Character.__init__(). 
        
        Arguments: 
        See Character.__init__(). 
        
        """ 
        
        Character.__init__(self, model, run, walk, startPoint, scale) 
        self.prevTurnTime = 0 
        self.setControl('up',1) 
    
    def move(self,task): 
        """Update the character for one frame. 
        
        Pick a new direction for the character to turn in every second. 
        Also see Character.move(). 
        
        Arguments: 
        See Character.move(). 
        
        Return: 
        See Character.move(). 
        
        """ 
        
        if task.time - self.prevTurnTime >= 1: 
            import random 
            direction = random.randint(1,3) 
            if direction == 1: 
                self.setControl('left',1) 
                self.setControl('right',0) 
            elif direction == 2: 
                self.setControl('left',0) 
                self.setControl('right',1) 
            elif direction == 3: 
                self.setControl('left',0) 
                self.setControl('right',0) 
            self.prevTurnTime = task.time 
        return Character.move(self,task) 

class Game(DirectObject): 
    """The game world -- environment, characters, camera, onscreen  text and 
    keyboard controls. 
    
    Public functions: 
    _init__ -- Initialise the game environment, characters, camera, onscreen 
               text and keyboard controls. 
    
    """ 
    
    def __init__(self): 
        # Accept the Esc key to quit the game. 
    
        self.accept("escape", sys.exit)
        
        self.startLogin()
        
    def startLogin(self):
        """Set up a login / server select GUI."""
        self.username = DirectEntry(scale=.08,pos=(.52,0,-.66),numLines=1,focus=1)
        
        self.password = DirectEntry(obscured=1,scale=.08,pos=(.52,0,-.86),numLines=1,focus=1)
        
        self.register = DirectButton(text = "Register",scale=.08,pos=(.96,0,-.96),command=Config.NETWORK.register)
        
        self.login = DirectButton(text = "Log In",scale=.08,pos=(1.23,0,-.96),command=self.startGame) #Config.NETWORK.login)
        
    def startGame(self):
        self.hideLogin()
        
        """Initialise the game environment and characters.""" 
        # Post some onscreen instructions. 

        title = addTitle("Nexus Demo") 
        # inst1 = addInstructions(0.95, "[ESC]: Quit") 
        # inst2 = addInstructions(0.90, "[Left Arrow]: Rotate Ralph Left") 
        # inst3 = addInstructions(0.85, "[Right Arrow]: Rotate Ralph Right") 
        # inst4 = addInstructions(0.80, "[Up Arrow]: Run Ralph Forward") 
        # inst4 = addInstructions(0.75, "[Down Arrow]: Run Ralph Backward") 
        # inst6 = addInstructions(0.65, "[A]: Rotate Camera Left") 
        # inst7 = addInstructions(0.60, "[S]: Rotate Camera Right") 

        # Initialise the environment. 

        base.win.setClearColor(Vec4(0,0,0,1)) 
        environ = loader.loadModel(Config.MYDIR+"/models/world/world")      
        environ.reparentTo(render) 
        environ.setPos(0,0,0)    
        environ.setCollideMask(BitMask32.bit(1)) 

        # Create a character for the player. 

        player = Character("/models/ralph/ralph", 
                        "/models/ralph/ralph-run", 
                        "/models/ralph/ralph-walk", 
                        environ.find("**/start_point").getPos(), 
                        .2) 
                        
        # Hook up some control keys to the character 
        
        self.accept("arrow_left", player.setControl, ["left",1]) 
        self.accept("arrow_right", player.setControl, ["right",1]) 
        self.accept("arrow_up", player.setControl, ["up",1]) 
        self.accept("arrow_down", player.setControl, ["down",1]) 
        
        # Stop event handling if the keys are lifted up
        self.accept("arrow_left-up", player.setControl, ["left",0])
        self.accept("arrow_right-up", player.setControl, ["right",0]) 
        self.accept("arrow_up-up", player.setControl, ["up",0]) 
        self.accept("arrow_down-up", player.setControl, ["down",0])
         
        # Create a camera to follow the player. 

        camera = Camera(player.actor) 
    
        # Accept some keys to move the camera. 

        self.accept("a-up", camera.setControl, ["left",0]) 
        self.accept("s-up", camera.setControl, ["right",0]) 
        self.accept("a", camera.setControl, ["left",1]) 
        self.accept("s", camera.setControl, ["right",1]) 
                        
        # Create some non-player characters. 
        # 
        # rex = Agent("/models/trex/trex", 
        #                 "/models/trex/trex-run", 
        #                 "/models/trex/trex-run", 
        #                 environ.find("**/start_point").getPos(), 
        #                 .2) 
        # 
        # eve = Agent("/models/eve/eve", 
        #                 "/models/eve/eve-walk", 
        #                 "/models/eve/eve-run", 
        #                 environ.find("**/start_point").getPos(), 
        #                 .2)   
                         
    def hideLogin(self):
        self.username.destroy()
        self.password.destroy()
        self.register.destroy()
        self.login.destroy()
    
def addInstructions(pos, msg): 
    """Put 'msg' on the screen at position 'pos'.""" 
    return OnscreenText(text=msg, style=1, fg=(1,1,1,1), 
            pos=(-1.3, pos), align=TextNode.ALeft, scale = .05) 

def addTitle(text): 
    """Put 'text' on the screen as the title.""" 
    return OnscreenText(text=text, style=1, fg=(1,1,1,1), 
                    pos=(1.3,-0.95), align=TextNode.ARight, scale = .07) 
        
if __name__ == "__main__":        
    
    game = Game() 
    run()