def conv_node(nodes, node) :
    print("Convert node type:{} name:{}".format(node.type, node.name))
    if node.type == 'MIX_SHADER':
       return nodes.new(type='ShaderNodeOctMixMat')
    elif node.type == 'BSDF_TRANSPARENT':
        # for Octane, there is an opacity input on most of shaders.
        # should be replaced by Opacity of Universal Material
        return nodes.new(type='ShaderNodeOctGlossyMat')
    elif node.type == 'BSDF_PRINCIPLED':
        return nodes.new(type='ShaderNodeOctUniversalMat')
    elif node.type == 'MIX_RGB':
        # FIXME: respect an operation mode, Multiply, Add... or more.
        # frac could be multipy to Color2:  result = Color1 op (Color2 * Fac)
        return nodes.new(type='ShaderNodeOctMixTex')
    elif node.type == 'HUE_SAT':
        # Octane has a good color collection node which can consolidate Hue/Sat and Bright/Contrast onto one.
        return nodes.new(type='ShaderNodeOctColorCorrectTex')
    elif node.type == 'BRIGHTCONTRAST':
        return nodes.new(type='ShaderNodeOctColorCorrectTex')
    elif node.type == 'TEX_IMAGE':
        # FIXME: Octane's tex nodes need to  be respective if it uses alpha or not
        return nodes.new(type='ShaderNodeOctImageTex')
    elif node.type == 'MAPPING':
        return nodes.new(type='ShaderNodeOct2DTransform')
    elif node.type == 'TEX_COORD':
        return nodes.new(type='ShaderNodeOctUVWProjection')
    return None

def get_equiv_link_input(nc, org) :
    (node, link) = org
    print("lookup for original INPUT link:[{}] type:{} name:{} of {}".format(link, node.inputs[link].type, node.inputs[link].name, node.name))
    return -1

def get_equiv_link_output(nc, org) :
    (node, link) = org
    print("lookup for original OUTPUT link:[{}] type:{} name:{} of {}".format(link, node.outputs[link].type, node.outputs[link].name, node.name))
    # just returns 0 mostly. perticular node has multi-outputs eg decomposing a vector
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
    nc = conv_node(newmat, node)
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

def convert_start(mat, out) :
    convert({}, None, mat, None, (out, 0), (out, 0))

def start(mat) :
    out = list(filter(lambda x: x.type == 'OUTPUT_MATERIAL' and x.is_active_output and x.target != 'OCTANE', mat.node_tree.nodes))
    [convert_start(mat, o) for o in out]
## start(bpy.context.active_object.active_material)
