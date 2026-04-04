#Landscape Homework

import bpy
from mathutils import noise
import bmesh
import math 
from math import *
factor = 2.8 # How far up and down the landscape goes
snow_level = 1.0 #How high for snow
water_level = -0.8 # What level is the water
frequency = 0.2 # affects gradient
height = 0.0 # Height offset of the landscape
subdivisions = 1000

def make_vertex_color_material():
    mat = bpy.data.materials.new(name="VertexColorMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    color_node = mat.node_tree.nodes.new(type='ShaderNodeVertexColor')
    color_node.layer_name = "Col"
    mat.node_tree.links.new(color_node.outputs['Color'], bsdf.inputs['Base Color'])
    return mat

def delete_all_objects():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def make_key(co):
    return (round(co[0], 3), round(co[1], 3))

delete_all_objects()

bpy.ops.mesh.primitive_grid_add(size=100.0, x_subdivisions=100, y_subdivisions=100, location=(0, 0, water_level+5))
obj = bpy.context.active_object
obj.data.materials.append(make_vertex_color_material())
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(obj.data)
bm.faces.ensure_lookup_table()
color_layer = bm.loops.layers.color.new("Col")
for i, face in enumerate(bm.faces):
    for loop in face.loops:
        loop[color_layer] = (0, 0, 1, .3)
bmesh.update_edit_mesh(obj.data)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.mesh.primitive_grid_add(size=100.0, x_subdivisions=subdivisions, y_subdivisions=subdivisions, location=(0, 0, 5))
step = 100.0 / subdivisions
obj = bpy.context.active_object
v_heights = {}
for v in obj.data.vertices:
    v.co.z += height + (noise.noise(frequency * v.co) * factor)
    v_heights[make_key((v.co.x, v.co.y))] = v.co.z
obj.data.materials.append(make_vertex_color_material())
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(obj.data)
bm.faces.ensure_lookup_table()
color_layer = bm.loops.layers.color.new("Col")
face_color = (1, 1, 1, 1)
for i, face in enumerate(bm.faces):
    for loop in face.loops:
        elev = loop.vert.co.z
        slope = 0
        water_direction = 0
        if abs(loop.vert.co.y) < 50 and abs(loop.vert.co.x) < 50 :
            e1 = v_heights[make_key((loop.vert.co.x - step, loop.vert.co.y + step))]
            e2 = v_heights[make_key((loop.vert.co.x + step, loop.vert.co.y - step))]
            s1 = e1 - e2
            e1 = v_heights[make_key((loop.vert.co.x, loop.vert.co.y + step))]
            e2 = v_heights[make_key((loop.vert.co.x, loop.vert.co.y - step))]
            s2 = e1 - e2
            e1 = v_heights[make_key((loop.vert.co.x + step, loop.vert.co.y + step))]
            e2 = v_heights[make_key((loop.vert.co.x - step, loop.vert.co.y - step))]
            s3 = e1 - e2
            e1 = v_heights[make_key((loop.vert.co.x + step, loop.vert.co.y))]
            e2 = v_heights[make_key((loop.vert.co.x - step, loop.vert.co.y))]
            s4 = e1 - e2
            slopes = [s1, s2, s3, s4]
            slope_values = [abs(s) for s in slopes]
            slope = max(slope_values)
            max_index = slope_values.index(slope)
            water_direction = max_index * pi/4
            if(slopes[max_index] < 0):
                water_direction += pi
#------------------------------------------------------------------------------------------------
#Color time
        if elev < water_level+ 0.2:      
            loop[color_layer] = (1, .9, .3, 1)
        elif abs(elev - water_level) < 1.5 and slope < 1.7:      
            loop[color_layer] = (0, .3, .1, 1)
        elif abs(elev + water_level) < 0.4:
            loop[color_layer] = (.35, .35, .35, 1)
        else:
            loop[color_layer] = (1, 1, 1, 1) 
        continue
        if slope > 0.5:
            loop[color_layer] = (.35, .35, .35, 1) 
        elif elev < water_level: # underwater
            loop[color_layer] = (0, 0, .3, 1)
        elif elev < snow_level:
            loop[color_layer] = (1, .8, .8, 1)
        else:
            loop[color_layer] = (1, 1, 1, 1)
bmesh.update_edit_mesh(obj.data)
bpy.ops.object.mode_set(mode='OBJECT')
#-----------------------------------------------------------------------------------------------
#Sun time
bpy.ops.object.light_add(type='SUN', radius=1, location=(0, -80, 60))
sun = bpy.context.active_object
sun.data.energy = 5
sun.data.angle = math.radians(5)
sun.name = "DaSun"

#Center of biome
constraint = sun.constraints.new(type='TRACK_TO')
constraint.target = obj
constraint.track_axis = 'TRACK_NEGATIVE_Z'
constraint.up_axis = 'UP_Y'

#Animation
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 250
positions = [
    (-80, -80, 10),  #sunrise
    (80, -80, 10)    #sunset 
]
frames = [1, 250]
for pos, frame in zip(positions, frames):
    sun.location = pos
    sun.keyframe_insert(data_path="location", frame=frame)

#Camera for picture
bpy.ops.object.camera_add(location=(0, -150, 80), rotation=(math.radians(60 ), 0, 0))
bpy.context.scene.camera = bpy.context.active_object
