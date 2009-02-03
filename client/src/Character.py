import direct.directbase.DirectStart 

import Config
import Controller

from pandac.PandaModules import CollisionTraverser,CollisionNode 
from pandac.PandaModules import CollisionHandlerQueue,CollisionRay 
from pandac.PandaModules import Filename 
from pandac.PandaModules import PandaNode,NodePath,Camera,TextNode 
from pandac.PandaModules import Vec3,Vec4,BitMask32 
from direct.gui.OnscreenText import OnscreenText 
from direct.actor.Actor import Actor 
from direct.task.Task import Task 
from direct.showbase.DirectObject import DirectObject 
import random, sys, os, math

class Character: 
    
    """A character with an animated avatar that moves left, right or forward 
       according to the controls turned on or off in self.controlMap. 
    
    Public fields: 
    self.controlMap -- The character's movement controls 
    self.actor -- The character's Actor (3D animated model) 
    
    
    Public functions: 
    __init__ -- Initialise the character 
    move -- Move and animate the character for one frame. This is a task 
            function that is called every frame by Panda3D. 
    setControl -- Set one of the character's controls on or off. 
    
    """ 

    def __init__(self, model, run, walk, startPos, scale):        
        """Initialise the character. 
        
        Arguments: 
        model -- The path to the character's model file (string) 
           run : The path to the model's run animation (string) 
           walk : The path to the model's walk animation (string) 
           startPos : Where in the world the character will begin (pos) 
           scale : The amount by which the size of the model will be scaled 
                   (float) 
                    
           """ 

        self.controlMap = {"left":0, "right":0, "up":0, "down":0} 

        self.actor = Actor(Config.MYDIR+model, 
                                 {"run":Config.MYDIR+run, 
                                  "walk":Config.MYDIR+walk})        
        self.actor.reparentTo(render) 
        self.actor.setScale(scale) 
        self.actor.setPos(startPos) 

        self.controller = Controller.LocalController(self)
        
        taskMgr.add(self.move,"moveTask") # Note: deriving classes DO NOT need 
                                          # to add their own move tasks to the 
                                          # task manager. If they override 
                                          # self.move, then their own self.move 
                                          # function will get called by the 
                                          # task manager (they must then 
                                          # explicitly call Character.move in 
                                          # that function if they want it). 
        self.prevtime = 0 
        self.isMoving = False 

        # We will detect the height of the terrain by creating a collision 
        # ray and casting it downward toward the terrain.  One ray will 
        # start above ralph's head, and the other will start above the camera. 
        # A ray may hit the terrain, or it may hit a rock or a tree.  If it 
        # hits the terrain, we can detect the height.  If it hits anything 
        # else, we rule that the move is illegal. 

        self.cTrav = CollisionTraverser() 

        self.groundRay = CollisionRay() 
        self.groundRay.setOrigin(0,0,1000) 
        self.groundRay.setDirection(0,0,-1) 
        self.groundCol = CollisionNode('ralphRay') 
        self.groundCol.addSolid(self.groundRay) 
        self.groundCol.setFromCollideMask(BitMask32.bit(1)) 
        self.groundCol.setIntoCollideMask(BitMask32.allOff()) 
        self.groundColNp = self.actor.attachNewNode(self.groundCol)
        self.groundHandler = CollisionHandlerQueue() 
        self.cTrav.addCollider(self.groundColNp, self.groundHandler) 

        # Uncomment this line to see the collision rays 
        # self.groundColNp.show() 

        #Uncomment this line to show a visual representation of the
        #collisions occuring 
        # self.cTrav.showCollisions(render) 

    def move(self, task): 
        """Move and animate the character for one frame. 
        
        This is a task function that is called every frame by Panda3D. 
        The character is moved according to which of it's movement controls 
        are set, and the function keeps the character's feet on the ground 
        and stops the character from moving if a collision is detected. 
        This function also handles playing the characters movement 
        animations. 

        Arguments: 
        task -- A direct.task.Task object passed to this function by Panda3D. 
        
        Return: 
        Task.cont -- To tell Panda3D to call this task function again next 
                     frame. 
        """ 
        
        elapsed = task.time - self.prevtime 

        # save the character's initial position so that we can restore it, 
        # in case he falls off the map or runs into something. 

        startpos = self.actor.getPos() 

        # pass on input
        self.controller.move(task, elapsed)
        
        # If the character is moving, loop the run animation. 
        # If he is standing still, stop the animation. 

        if (self.controlMap["up"]!=0) or (self.controlMap["left"]!=0) or (self.controlMap["right"]!=0) or (self.controlMap["down"]!=0): 
            
            if self.isMoving is False: 
                self.actor.loop("run") 
                self.isMoving = True 
        else: 
            if self.isMoving: 
                self.actor.stop() 
                self.actor.pose("walk",5) 
                self.isMoving = False 

        # Now check for collisions. 

        self.cTrav.traverse(render) 

        # Adjust the character's Z coordinate.  If the character's ray hit terrain, 
        # update his Z. If it hit anything else, or didn't hit anything, put 
        # him back where he was last frame. 

        entries = [] 
        for i in range(self.groundHandler.getNumEntries()): 
            entry = self.groundHandler.getEntry(i) 
            entries.append(entry) 
        entries.sort(lambda x,y: cmp(y.getSurfacePoint(render).getZ(), 
                                     x.getSurfacePoint(render).getZ())) 
        if (len(entries)>0) and (entries[0].getIntoNode().getName() == "terrain"):
            self.actor.setZ(entries[0].getSurfacePoint(render).getZ()) 
        else: 
            self.actor.setPos(startpos) 

        # Store the task time and continue. 
        self.prevtime = task.time 
        return Task.cont 

    def setControl(self, control, value): 
        """Set the state of one of the character's movement controls. 
        
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