# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/00_representation.ipynb (unless otherwise specified).

__all__ = ['Representation', 'Node']

# Cell
from fastai.vision.all import *

# Cell
class Representation:
    'Representation of a Learn object.'
    def __init__(self, data): self.data = data
    def __repr__(self): return f'{self.__class__.__name__} (\n{self.data}\n)'

# Cell
class Node:
    "Represents a Module or Parameter."
    def __init__(self, name, idx, typ, obj=None, nodes=None, links=None, xtra=None):
        store_attr('name,idx,typ,obj', self)
        self.nodes = ifnone(nodes, [])
        self.links = ifnone(links, [])
        self.xtra  = ifnone(xtra , {})

    def __repr__(self):
        res = f'({self.__class__.__name__}): {self.name}, type: {self.typ}, idx={self.idx}'
        if len(self.xtra): res += f'\nxtra: {self.xtra}'
        if len(self.nodes):
            res += '\nnodes: ['
            for node in self.nodes: res += f'\n  {node}'
            res += '\n]'

        if len(self.links):
            res += '\nlinks: ['
            for link in self.links: res += f'\n  {link}'
            res += '\n]'

        return res

# Cell
@patch
def to_representation(self:nn.Module, name=None, idx=0, path=None, xtra=None):
    "Obtain information of the Module and stores it on a `Node`."
    name = ifnone(name, self.__class__.__name__)
    xtra = ifnone(xtra, {})
    if path is not None: xtra['path'] = path
    typ = 'Sequential' if isinstance(self, nn.Sequential) else 'Module'
    nodes,links = _get_module_nodes(self)
    if hasattr(self, '_xtra'): xtra.update(self._xtra)
    return Node(name, idx, typ, self, nodes, links, xtra)

def _get_module_nodes(module:nn.Module):
    "Obtain the `Node` representation for all the module childrens."
    nodes,links = [],[]
    is_seq = isinstance(module, nn.Sequential)
    for i,(n,m) in enumerate(module.named_children()):
        name = f'{n}_{m.__class__.__name__}' if is_seq else n
        nodes.append(m.to_representation(name, i, n))
        if i>0: links.append({'source':i-1, 'target':i})

    return nodes,links

# Cell
@patch
def to_representation(self:Learner):
    "Gets a representation of the Learner to be passed to a web client."
    xb,yb = self.dls.train.one_batch()
    def _get_info(m, i, o):
        params,trainable = total_params(m)
        m._xtra = {'params': params, 'trainable': trainable, 'shape': o.shape}

    model = self.model.to(xb.device)
    layers = flatten_model(model)
    with Hooks(layers, _get_info) as h: model.eval()(xb)

    nodes = [Node('Input', 0, 'Input', xtra={'shape':list(xb.shape)}),
             self.model.to_representation(xtra={'open': True}),
             Node('Output', 0, 'Output')]
    links = [{'source':i, 'target':i+1} for i in range_of(nodes)]
    rep = Representation(Node('Learner', 0, 'Learner', nodes=nodes, links=links, xtra={'open': True}))
    _update_shapes(rep.data)
    for layer in layers: del(layer._xtra) # Clean
    nodes[-1].xtra['shape'] = nodes[-2].xtra.get('shape')
    return rep

def _update_shapes(node):
    shape = node.xtra.get('shape')
    childs = node.nodes
    if (shape is None) and len(childs):
        for n in node.nodes: _update_shapes(n)
        node.xtra['shape'] = childs[-1].xtra.get('shape')

# Cell
@patch
def get_dict(self:Node):
    "Gets the dictionary of the `Node`."
    res = {'name':self.name, 'type':self.typ, 'index':self.idx}
    if len(self.nodes): res['nodes'] = [o.get_dict() for o in self.nodes]
    if len(self.links): res['links'] = self.links
    if len(self.xtra) : res['xtra']  = self.xtra
    return res

# Cell
@patch
def to_json(self:Representation):
    "Gets the seriable json from the Leaner `Representation`."
    return json.dumps(self.data.get_dict())