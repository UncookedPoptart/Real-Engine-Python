import model
import mesh
import glm
from material_handler import MaterialHandler
from hitboxes import *
from physics_engine import PhysicsEngine
from random import randint

class ObjectHandler:
    def __init__(self, scene):
        self.scene = scene
        self.ctx = scene.ctx
        self.objects = {'container' : [], 'metal_box' : [], 'cat' : [], 'meshes' : [], 'skybox' : []}

        self.light_handler = self.scene.light_handler

        self.material_handler = MaterialHandler(self.scene.texture_handler.textures)
        
        # Physics
        self.pe = PhysicsEngine(-9.8)

        self.on_init()

    def on_init(self):

        self.objects['skybox'].append(Object(self, self.scene, model.SkyBoxModel, vao='skybox', immovable = True, gravity = False))
        for i in range(20):
            self.objects['metal_box'].append(Object(self, self.scene, model.BaseModel, pos=(randint(-20, 20), randint(-30, 0), randint(-20, 20)), scale=(5, 0.5, 5), rot = (randint(-180, 180), randint(-180, 180), randint(-180, 180)),material='metal_box', immovable = True, gravity = False))
        for i in range(20):
            self.objects['metal_box'].append(Object(self, self.scene, model.BaseModel, pos=(randint(-20, 20), randint(10, 20), randint(-20, 20)), scale=(0.5, 0.5, 0.5), material='metal_box'))
        #self.objects['metal_box'].append(Object(self, self.scene, model.BaseModel, pos=(-10, 1, 1), scale=(.25, .25, .25), material='metal_box', immovable = True, gravity = False))
        #self.objects['metal_box'].append(Object(self, self.scene, model.BaseModel, pos=(10, 1, 15), scale=(.25, .25, .25), material='metal_box', immovable = True, gravity = False))

        #self.objects['meshes'].append(Object(self, self.scene, model.BaseModel, vao='terrain', pos=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), material='metal_box', immovable = True, gravity = False))

    def update(self, delta_time):
    
        movable_objects = []
        for category in self.objects:
            if category == 'skybox': continue
            category_list = self.objects[category]
            for obj in category_list: 
                
                movable_objects.append(obj)   
                if obj.immovable: continue    
                
                # changes pos of all models in scene based off hitbox vel
                obj.move_tick(delta_time)
                
                if obj.pos[1] < -30: 
                    obj.set_pos(glm.vec3(randint(-20, 20), randint(10, 20), randint(-20, 20)))
                    #obj.set_pos(glm.vec3(0, 10, 0))
                    obj.hitbox.set_vel(glm.vec3(0, 0, 0))
                    
                obj.hitbox.move_tick(delta_time, glm.vec3(0, self.pe.gravity_strength, 0), glm.vec3(0, 0, 0))
                    
        self.pe.resolve_collisions(movable_objects, delta_time)

    def apply_shadow_shader_uniforms(self):
        programs = self.scene.vao_handler.program_handler.programs
        for program in programs:
            if program == 'default' or program == 'mesh':
                programs[program]['m_view_light'].write(self.light_handler.dir_light.m_view_light)
                programs[program]['u_resolution'].write(glm.vec2(self.scene.graphics_engine.app.win_size))
                self.depth_texture = self.scene.texture_handler.textures['depth_texture']
                programs[program]['shadowMap'] = 3
                self.depth_texture.use(location=3)

    def render_shadows(self):
        self.apply_shadow_shader_uniforms()
        # Render Models
        programs = self.scene.vao_handler.program_handler.programs
        programs['shadow_map']['m_view_light'].write(self.light_handler.dir_light.m_view_light)
        for obj_type in self.objects:
            if obj_type != 'skybox':
                for obj in self.objects[obj_type]:
                    obj.render_shadow()
    
    def render(self):
        programs = self.scene.vao_handler.program_handler.programs
        for obj_type in self.objects:
            for program in programs:
                if obj_type in ('container', 'metal_box', 'cat') and program == 'default':
                    # Materials
                    self.material_handler.materials[obj_type].write(programs[program])
                    # Lighting
                    self.light_handler.write(programs[program])
                    # Basic Rendering
                    programs[program]['view_pos'].write(self.scene.graphics_engine.camera.pos)
                    programs[program]['m_view'].write(self.scene.graphics_engine.camera.m_view)
                if obj_type in ('skybox') and program == 'skybox':
                    programs[program]['m_view'].write(glm.mat4(glm.mat3(self.scene.graphics_engine.camera.m_view)))
                    programs[program]['u_texture_skybox'] = 0
                    self.scene.texture_handler.textures['skybox'].use(location=0)
                if obj_type in ('meshes') and program == 'mesh':
                    # Lighting
                    self.light_handler.write(programs[program])
                    programs[program]['view_pos'].write(self.scene.graphics_engine.camera.pos)
                    # Basic Rendering
                    programs[program]['m_view'].write(self.scene.graphics_engine.camera.m_view)

            for obj in self.objects[obj_type]:
                obj.render()


class Object:
    def __init__(self, obj_handler, scene, model, vao='cube', material='container', pos=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), hitbox_type = 'cube', hitbox_file_name = None, rot_vel = (0, 0, 0), vel = (0, 0, 0), mass = 1, immovable = False, gravity = True):
        
        # init variables
        self.ctx = obj_handler.ctx
        self.camera = scene.graphics_engine.camera
        self.scene = scene

        # material
        self.material = obj_handler.material_handler.materials[material] 

        # model matrix variables
        self.pos = glm.vec3(pos)
        self.rot = glm.vec3([glm.radians(a) for a in rot])
        self.scale = glm.vec3(scale)
        
        # physics variables
        self.immovable = immovable
        self.gravity = gravity
        self.mass = mass if not immovable else 1e10

        self.on_init(model, vao=vao, hitbox_type=hitbox_type, hitbox_file_name=hitbox_file_name, rot_vel=rot_vel, vel=vel)

    def on_init(self, model, vao='cube', hitbox_type = 'cube', hitbox_file_name = None, rot_vel = (0, 0, 0), vel = (0, 0, 0)):
        self.model = model(self, self.scene, vao)

        self.hitbox = None
        match hitbox_type:
            case 'cube': self.define_hitbox_cube(vel, rot_vel)
            case 'rectangle': self.define_hitbox_rectangle(hitbox_file_name, vel, rot_vel)
            case 'fitted': self.define_hitbox_fitted(hitbox_file_name, vel, rot_vel)
            case _: assert False, 'hitbox type is not recognized'
            
    def render(self):
        self.model.rot = glm.vec3([glm.radians(a) for a in self.rot])
        self.model.render()
    
    def render_shadow(self):
        self.model.render_shadow()
        
    def define_hitbox_cube(self, vel, rot_vel):
        self.hitbox = CubeHitbox(self, vel, rot_vel)
            
    def define_hitbox_rectangle(self, file_name, vel, rot_vel):
        assert file_name != None, 'hitbox needs file name to be created'
        self.hitbox = FittedHitbox(self, file_name, True, vel, rot_vel)
    
    def define_hitbox_fitted(self, file_name, vel, rot_vel):
        assert file_name != None, 'hitbox needs file name to be created'
        self.hitbox = FittedHitbox(self, file_name, False, vel, rot_vel)
        
    # for physics
    def move_tick(self, delta_time):
        
        self.pos += delta_time * self.hitbox.vel
        self.rot += delta_time * self.hitbox.rot_vel
        self.model.update()
        
    def move_tick_translate(self, delta_time):
        
        self.pos += delta_time * self.hitbox.vel
        self.model.update()
        
    def move_tick_rot(self, delta_time):
        
        self.rot += delta_time * self.hitbox.rot_vel
        self.model.update()
        
    def set_hitbox(self, hitbox):
        
        self.hitbox = hitbox
        
    def get_cartesian_vertices(self):
        
        vertices = [self.model_matrix * vertex for vertex in self.hitbox.vertices]
        return vertices
    
    def set_pos(self, pos):
        
        self.pos = pos