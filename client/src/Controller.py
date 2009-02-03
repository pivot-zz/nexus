class LocalController:
    """Receives input and acts based on it."""
    def __init__(self,avatar):
        self.avatar = avatar
        self.actor = avatar.actor
        
    def forward(self):
        backward = self.actor.getNetTransform().getMat().getRow3(1) 
        backward.setZ(0) 
        backward.normalize() 
        self.actor.setPos(self.actor.getPos() - backward*(self.elapsed*5))
        
    def up(self):
        if (self.actor.getH() != 0):
            self.actor.setH(0)
        self.forward()
        
    def right(self):
        if (self.actor.getH() != -90):
            self.actor.setH(-90) 
        self.forward()
        
    def left(self):
        if (self.actor.getH() != 90):
            self.actor.setH(90) 
        self.forward()
        
    def down(self):
        if (self.actor.getH() != 180):
            self.actor.setH(180)
        self.forward()
        
    def move(self, task, elapsed):
        self.elapsed = elapsed
        if (self.avatar.controlMap["left"]!=0): 
            self.left()
        if (self.avatar.controlMap["right"]!=0): 
            self.right()
        if (self.avatar.controlMap["up"]!=0): 
            self.up()
        if (self.avatar.controlMap["down"]!=0): 
            self.down()