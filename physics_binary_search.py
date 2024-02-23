import glm
from gjk import *

class PBS():
    
    def __init__(self, pe):
        
        self.gjk = GJK()
        self.pe = pe
        
        # binary search variables
        self.low = 0
        self.high = 0
        self.best = 0
        self.mid = 0
        
        # vel variables
        self.orig_vel1, self.orig_vel2 = 0, 0
        self.temp_vel1, self.temp_vel2 = 0, 0
        
        # rot variables
        self.rot_vel1 = 0
        self.rot_vel2 = 0
        
    def uncollide_objects(self, obj1, obj2, delta_time):
        
        for direction in [1, 2, 0]:
            self.translational_binary_search(obj1, obj2, delta_time, direction)
        self.translational_binary_search(obj1, obj2, delta_time, direction)
            
    def setup_translate(self, vel1, vel2, delta_time, direction):
        
        self.setup_reset(delta_time)
        self.orig_vel1, self.orig_vel2 = vel1, vel2
        self.temp_vel1[direction] = vel1[direction]
        self.temp_vel2[direction] = vel2[direction]
    
    def setup_reset(self, delta_time): 
        
        # resets vel values
        self.temp_vel1 = [0, 0, 0]
        self.temp_vel2 = [0, 0, 0]

        # resets binary search variables
        self.high, self.low = delta_time, 0
        self.best = self.low
    
    # takes in two objects and moves them, no need to return
    def translational_binary_search(self, obj1, obj2, delta_time, direction, iterations = 3):
        
        self.setup_translate(obj1.hitbox.vel, obj2.hitbox.vel, delta_time, direction)

        if not obj1.immovable: obj1.hitbox.set_vel(glm.vec3(*self.temp_vel1))
        if not obj2.immovable: obj2.hitbox.set_vel(glm.vec3(*self.temp_vel2))
        
        for i in range(iterations):
            # determines mid-point of time
            self.mid = (self.high + self.low) / 2
            
            # moves objects to temporary points
            self.dual_move_tick_translate(obj1, obj2, self.mid)
            
            # determines if objects have collided
            collided, simp = self.gjk.get_gjk_collision(obj1.hitbox, obj2.hitbox)
            if collided: self.high = self.mid * 0.8
            else: self.low, self.best = self.mid * 1.2, self.mid
            
            # resets objects
            self.dual_move_tick_translate(obj1, obj2, -self.mid)
            
        self.dual_move_tick_translate(obj1, obj2, self.best)
        
        # resets vel to original 
        if not obj1.immovable: obj1.hitbox.set_vel(self.orig_vel1)
        if not obj2.immovable: obj2.hitbox.set_vel(self.orig_vel2)
        
    def rot_binary_search(self, obj1, obj2, delta_time, direction, iterations = 3):
        
        self.setup_reset(obj1.hitbox.vel, obj2.hitbox.vel, delta_time, direction)
        
        for i in range(iterations):
            # determines mid-point of time
            self.mid = (self.high + self.low) / 2
            
            # moves objects to temporary points
            self.dual_move_tick_rot(obj1, obj2, self.mid)
            
            # determines if objects have collided
            collided, simp = self.gjk.get_gjk_collision(obj1.hitbox, obj2.hitbox)
            if collided: self.high = self.mid * 0.8
            else: self.low, self.best = self.mid * 1.2, self.mid
            
            # resets objects
            self.dual_move_tick_rot(obj1, obj2, -self.mid)
            
        self.dual_move_tick_rot(obj1, obj2, self.best)
        
    # moves either position, rot, or both depending on the time that has passed for both objs
    def dual_move_tick(self, obj1, obj2, time):
        if self.is_moveable_forwards(obj1, obj2): obj1.move_tick(time)
        if self.is_moveable_forwards(obj2, obj1): obj2.move_tick(time)
        
    def dual_move_tick_translate(self, obj1, obj2, time):
        if self.is_moveable_forwards(obj1, obj2): obj1.move_tick_translate(time)
        if self.is_moveable_forwards(obj2, obj1): obj2.move_tick_translate(time)
        
    def dual_move_tick_rot(self, obj1, obj2, time):
        if not obj1.immovable: obj1.move_tick(time)
        if not obj2.immovable: obj2.move_tick(time)
        
    # detects if a physics body is moving towards an object and is not imovable
    def is_moveable_forwards(self, obj1, obj2):
        return not obj1.immovable and glm.dot(obj2.hitbox.get_center() - obj1.hitbox.get_center(), obj1.hitbox.vel) > 0