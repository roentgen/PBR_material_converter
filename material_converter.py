import bpy

def conv_node(nodes, node) :
    print("Convert node type:{} name:{}".format(node.type, node.name))
    loc = node.location
    ret = None
    if node.type == 'MIX_SHADER':
       ret = nodes.new(type='ShaderNodeOctMixMat')
       ret.inputs[0].default_value = node.inputs[0].default_value # Frac -> Amount
    elif node.type == 'BSDF_TRANSPARENT':
        # for Octane, there is an opacity input on most of shaders.
        # should be replaced by Opacity of Universal Material
        ret = nodes.new(type='ShaderNodeOctGlossyMat')
    elif node.type == 'BSDF_PRINCIPLED':
        ret = nodes.new(type='ShaderNodeOctUniversalMat')
        ret.transmission_type = 'OCT_BXDF_TRANSMISSION_TYPE_DIFFUSE'
        ret.brdf_model = 'OCTANE_BRDF_GGX'
        if node.inputs['Specular'].is_linked == False:
            ret.inputs['Specular'].default_value = node.inputs['Specular'].default_value
        if node.inputs['Metallic'].is_linked == False:
            ret.inputs['Metallic'].default_value = node.inputs['Metallic'].default_value
        if node.inputs['Roughness'].is_linked == False:
            ret.inputs['Roughness'].default_value = node.inputs['Roughness'].default_value
        if node.inputs['Anisotropic'].is_linked == False:
            ret.inputs['Anisotropy'].default_value = node.inputs['Anisotropic'].default_value
        if node.inputs['Anisotropic Rotation'].is_linked == False:
            ret.inputs['Rotation'].default_value = node.inputs['Anisotropic Rotation'].default_value
    elif node.type == 'MIX_RGB':
        # FIXME: respect an operation mode, Multiply, Add... or more.
        # frac could be multiply to Color2:  result = Color1 op (Color2 * Fac)
        if node.blend_type == 'MULTIPLY':
            ret = nodes.new(type='ShaderNodeOctMultiplyTex')
        else:
            ret = nodes.new(type='ShaderNodeOctMixTex')
            if node.inputs['Fac'].is_linked == False:
                ret.inputs['Amount'].default_value = node.inputs['Fac'].default_value
    elif node.type == 'HUE_SAT':
        # Octane has a good color collection node which can consolidate Hue/Sat and Bright/Contrast onto one.
        ret = nodes.new(type='ShaderNodeOctColorCorrectTex')
        if node.inputs['Hue'].is_linked == False:
            ret.inputs['Hue'].default_value = node.inputs['Hue'].default_value * 2
        if node.inputs['Saturation'].is_linked == False:
            ret.inputs['Saturation'].default_value = node.inputs['Saturation'].default_value
        if node.inputs['Value'].is_linked == False:
            ret.inputs['Gain'].default_value = node.inputs['Value'].default_value
        if node.inputs['Fac'].is_linked == False:
            ret.inputs['Mask'].default_value = node.inputs['Fac'].default_value
    elif node.type == 'BRIGHTCONTRAST':
        ret = nodes.new(type='ShaderNodeOctColorCorrectTex')
        if node.inputs['Bright'].is_linked == False:
            # Octane's Brightness is default 1.0 and will not get it lighter
            if node.inputs['Bright'].default_value > 0:
                ret.inputs['Exposure'].default_value = node.inputs['Bright'].default_value
            else:
                ret.inputs['Brightness'].default_value = node.inputs['Bright'].default_value
        if node.inputs['Contrast'].is_linked == False:
            ret.inputs['Contrast'].default_value = node.inputs['Contrast'].default_value
    elif node.type == 'TEX_IMAGE':
        # FIXME: Octane's tex nodes need to  be respective if it uses alpha or not
        # image: 
        # interpolation: LINEAR
        # projection: FLAT
        # extension: REPEAT
        ret = nodes.new(type='ShaderNodeOctImageTex')
        ret.image = node.image
        if node.extension == 'REPEAT':
            ret.border_mode = 'OCT_BORDER_MODE_WRAP'
        elif node.extension == 'EXTEND':
            ret.border_mode = 'OCT_BORDER_MODE_CLAMP' 
        elif node.extension == 'CLIP':
            ret.border_mode = 'OCT_BORDER_MODE_BLACK'
    elif node.type == 'MAPPING':
        ret = nodes.new(type='ShaderNodeOct2DTransform')
    elif node.type == 'TEX_COORD':
        ret = nodes.new(type='ShaderNodeOctUVWProjection')
    elif node.type == 'VALTORGB':
        ret = nodes.new(type='ShaderNodeOctClampTex')
    elif node.type == 'GAMMA':
        ret = nodes.new(type='ShaderNodeOctColorCorrectTex')
        if node.inputs['Gamma'].is_linked == False:
            ret.inputs['Gamma'].default_value = node.inputs['Gamma'].default_value
    elif node.type == 'INVERT':
        if node.inputs['Fac'].default_value == 0:
            ret = nodes.new(type='ShaderNodeOctAddTex') # ignorable
        else:
            ret = nodes.new(type='ShaderNodeOctInvertTex')
    elif node.type == 'NORMAL_MAP':
        # should be through
        ret = nodes.new(type='ShaderNodeOctAddTex')
    elif node.type == 'COMBXYZ':
        ret = nodes.new(type='ShaderNodeOctChannelMergerTex')
    elif node.type == 'SEPXYZ':
        # decomposing gonna be a group which has 3 output because Octane node only has 1 output
        ret = nodes.new("ShaderNodeGroup")
        ret.node_tree = bpy.data.node_groups['DecompVectorOct']
    if ret != None:
        ret.location = loc
    else:
        print("unknown org node: type:{} name:{}".format(node.type, node.name))
    return ret

def get_equiv_link_input(nc, org) :
    (node, link) = org
    print("lookup for original INPUT link:[{}] type:{} name:{} of {}".format(link, node.inputs[link].type, node.inputs[link].name, node.name))
    if node.type == 'TEX_IMAGE':
        # FIXME: need to branch Projection(5)/Transform(4)
        return 5
    elif node.type == 'MIX_SHADER' and link < 3:
        return link
    elif node.type == 'BSDF_PRINCIPLED':
        if link == 0: return 1    # diffuse color
        elif link == 4: return 2 # metallic
        elif link == 5: return 3 # specular
        elif link == 7: return 4 # roughness
        elif link == 20: return 29 # normal
    elif node.type == 'MIX_RGB':
        if node.blend_type == 'MULTIPLY':
            return link - 1
        return link
    elif node.type == 'VALTORGB':
        return link
    elif node.type == 'BRIGHTCONTRAST':
        if link == 0: return 0
        elif link == 1: return 1 # Bright
        elif link == 2: return 6 # Contrast
    elif node.type == 'HUE_SAT':
        if link == 0: return 3   # Hue
        elif link == 1: return 4 # Sat
        elif link == 2: return 7 # Value->Gain
        elif link == 3: return 9 # Fac->Mask
        elif link == 4: return 0
    elif node.type == 'GAMMA':
        if link == 0: return 0
        elif link == 1: return 5 # gamma
    elif node.type == 'INVERT':
        if link == 0: print("Error: ShaderNodeOctInvertTex has no factor")
        elif link == 1: return 0
    elif node.type == 'COMBXYZ':
        return link
    elif node.type == 'SEPXYZ':
        return link
    elif node.type == 'MAPPING':
        return link
    
    return -1

def get_equiv_link_output(nc, org) :
    (node, link) = org
    print("lookup for original OUTPUT link:[{}] type:{} name:{} of {}".format(link, node.outputs[link].type, node.outputs[link].name, node.name))
    # just returns 0 mostly. perticular node has multi-outputs eg decomposing a vector
    if node.type == 'SEPXYZ':
        return link
    return 0

## connect link new one's output to parent's input 
def connect(newmat, nc, parent, inputorg, org) :
    newlink_input = get_equiv_link_input(parent, org)
    newlink_output = get_equiv_link_output(nc, inputorg)
    if  newlink_input >= 0 and newlink_output >= 0:
        newmat.links.new(nc.outputs[newlink_output], parent.inputs[newlink_input])

def convert(visit, newmat, mat, parent, inputnode, org) :
    (node, __) = inputnode
    if node.as_pointer() in visit:
        nc = visit[node.as_pointer()]
        # what visit has key means a node gonna be not root (parent != None)
        connect(newmat, nc, parent, inputnode, org)
        return # do not descend, just link it 
    nc = conv_node(newmat.nodes, node)
    visit[node.as_pointer()] = nc
    # link newone to parent
    if parent != None:
         connect(newmat, nc, parent,  inputnode, org)
    items = node.inputs.items()
    # descends DAG
    for pair in items:
        if pair[1].is_linked:
            idx = items.index(pair)
            # link, is identified as node's idx-th input, links ports from next node's oidx-th (output) to node's idx-th:
            # where you can see to_node <-> from_node and to_socket <-> from_socket as dual edges of a link,
            # but I have to prefer from_node.outputs  so that I want to identifiy index of an output.
            link = node.inputs[idx].links[0]
            outs = link.from_node.outputs
            oidx = outs.values().index(link.from_socket)
            print("===> descend to link[{}]: name:{}  : node:{} -> node:{}".format(idx, pair[0], node.name, link.from_node.name))
            convert(visit, newmat, mat, nc,  (link.from_node, oidx), (node, idx))

def create_utilities() :
    # add Decompose Vector as a group
    g = bpy.data.node_groups.new('DecompVectorOct', 'ShaderNodeTree')
    gi = g.nodes.new('NodeGroupInput') # assign 1 input
    g.inputs.new('NodeSocketVector','Vec')
    go = g.nodes.new('NodeGroupOutput') # assign 3 outputs
    g.outputs.new('NodeSocketFloat', 'X')
    g.outputs.new('NodeSocketFloat', 'Y')
    g.outputs.new('NodeSocketFloat', 'Z')
    pickr = g.nodes.new('ShaderNodeOctChannelPickerTex')
    pickr.channel = 'OCT_CHANNEL_R'
    pickg = g.nodes.new('ShaderNodeOctChannelPickerTex')
    pickg.channel = 'OCT_CHANNEL_G'
    pickb = g.nodes.new('ShaderNodeOctChannelPickerTex')
    pickb.channel = 'OCT_CHANNEL_B'
    g.links.new(gi.outputs['Vec'], pickr.inputs[0])
    g.links.new(gi.outputs['Vec'], pickg.inputs[0])
    g.links.new(gi.outputs['Vec'], pickb.inputs[0])
    g.links.new(pickr.outputs[0], go.inputs['X'])
    g.links.new(pickg.outputs[0], go.inputs['Y'])
    g.links.new(pickb.outputs[0], go.inputs['Z'])
    
def convert_start(mat, out) :
    create_utilities()
    name = mat.name
    newmat = bpy.data.materials.new(name=name)
    newmat.use_nodes = True
    bpy.context.active_object.data.materials.append(newmat)
    convert({}, newmat.node_tree, mat.node_tree, None, (out, 0), (out, 0))

def start(mat) :
    mat.use_nodes = True
    out = list(filter(lambda x: x.type == 'OUTPUT_MATERIAL' and x.is_active_output and x.target != 'OCTANE', mat.node_tree.nodes))
    [convert_start(mat, o) for o in out]
## start(bpy.context.active_object.active_material)

def dryrun(mat):
    print("dryrun: ")
    out = list(filter(lambda x: x.type == 'OUTPUT_MATERIAL' and x.is_active_output and x.target != 'OCTANE', mat.node_tree.nodes))
    [print("conv_start() for {}".format(o)) for o in out]
    print("dryrun: finished")
