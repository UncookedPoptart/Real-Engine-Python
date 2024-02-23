import glm    

class GJK():
    
    def __init__(self):
        
        self.reset()
        
    def reset(self):
        
        self.simplex = []
    
    # accurate collision detection between two convex shapes
    def get_gjk_collision(self, hitbox1, hitbox2):
        
        self.reset()
        
        # find starting vector
        vec = -1 * (hitbox2.get_center() - hitbox1.get_center())
        self.simplex = [self.get_support_point(hitbox1, hitbox2, vec)]
        
        # point vector towards the origin
        vec = -self.simplex[0][0] # may need to be changed to mult -1
        for i in range(25):
            
            # gets furthest point across from origin
            a = self.get_support_point(hitbox1, hitbox2, vec)

            # checks if point made it across the origin
            if glm.dot(a[0], vec) < 0: return False, None
            self.simplex.append(a)
            
            check, vec = self.handle_simplex()
            if check: return True, self.simplex
        
        else: return False, None
            
    def get_support_point(self, hitbox1, hitbox2, vec):
    
        # furthest point in model1 - model2
        far1, far2 = self.get_furthest_point(hitbox1, vec), self.get_furthest_point(hitbox2, -vec)
        return far1 - far2, (far1, far2)
    
    def get_furthest_point(self, hitbox, vec):
    
        # finds furthest point in given direction
        best = (glm.vec3(0, 0, 0), -1e6)
        for point in hitbox.get_vertices():
            dot = glm.dot(point, vec)
            if dot > best[1]: best = (point, dot)
            
        return best[0]
    
    # handles operations for symplex with given range
    def handle_simplex(self):
        
        match len(self.simplex):
            case 2: return self.handle_simplex_line()
            case 3: return self.handle_simplex_triangle()
            case 4: return self.handle_simplex_tetra()
            case _: assert False, 'simplex has unsupported size :('
            
    def handle_simplex_line(self): # when simplex has two points
    
        vec_ab, vec_ao = self.simplex[1][0] - self.simplex[0][0], -self.simplex[0][0]
        vec_ab_perp = self.triple_product(vec_ab, vec_ao, vec_ab)
        
        # returns false since origin cannot be contained on a line and the perpendicular vector
        return False, vec_ab_perp
    
    def handle_simplex_triangle(self):
    
        vec_ab, vec_ac, = self.simplex[1][0] - self.simplex[0][0], self.simplex[2][0] - self.simplex[0][0]
        vec = glm.cross(vec_ac, vec_ab)
        
        # points vector towards the origin
        vec_ao = -self.simplex[0][0]
        if glm.dot(vec, vec_ao) < 0: vec = -vec
        
        return False, vec
    
    def handle_simplex_tetra(self):
    
        vec_da = self.simplex[3][0] - self.simplex[0][0]
        vec_db = self.simplex[3][0] - self.simplex[1][0]
        vec_dc = self.simplex[3][0] - self.simplex[2][0]
        vec_do = -self.simplex[3][0]
        
        
        if glm.dot(bcd_normal_vec := glm.cross(vec_db, vec_dc), vec_do) >= 0:
            self.simplex.pop(0)
            return False, bcd_normal_vec
        elif glm.dot(cad_normal_vec := glm.cross(vec_dc, vec_da), vec_do) >= 0:
            self.simplex.pop(1)
            return False, cad_normal_vec
        elif glm.dot(abd_normal_vec := glm.cross(vec_da, vec_db), vec_do) >= 0:
            self.simplex.pop(2)
            return False, abd_normal_vec
        else:
            return True, None
    
    def triple_product(self, vec1, vec2, vec3):
    
        return glm.cross(glm.cross(vec1, vec2), vec3)