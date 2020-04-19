# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/00_representation.ipynb (unless otherwise specified).

__all__ = ['Representation']

# Cell
from fastai2.vision.all import *

# Cell
class Representation:
    'Representation of a Model'
    def __init__(self, name, inp_shape, out_shape, modules=None, params=None, links=None, xtra=None):
        store_attr(self, 'name,inp_shape,out_shape,modules,params,links')
        self.xtra = ifnone(xtra, dict())

    def __repr__(self):
        return (f'{self.name} {self.inp_shape} -> {self.out_shape} (\n' +
                f'  modules: {self.modules}\n' +
                f'  params: {self.params}\n' +
                f'  links: {self.links}\n' +
                f'  xtra: {self.xtra}\n' +
                 ')')

# Cell
@patch
def to_representation(self:nn.Module, *xb):
    "Gets a summary of `self` using `xb`"
    sample_inputs,infos = layer_info(self, *xb)
    n,bs = 64,find_bs(xb)
    name = self.__class__.__name__
    modules,params,links,xtra = L(),L(),L(),{}
    inp_shape = list(apply(lambda x:x.shape, xb)[0])
    out_shape = list(apply(lambda x:x.shape, xb)[0])
    infos = L([o for o in infos if o is not None]) #see comment in previous cell
    for i,(typ,np,trn,sz) in infos.enumerate():
        modules.append({'idx':i, 'name':typ})

    if isinstance(self, nn.Sequential):
        idxs = modules.map(lambda x: x['idx'])
        links = idxs[:-1].map_zipwith(lambda a,b: {'source':a, 'target':b}, idxs[1:])
    else: raise NotImplementedError()

    return Representation(name, inp_shape, out_shape, modules, params, links, xtra)

    inp_sz = _print_shapes(apply(lambda x:x.shape, xb), bs)
    res = f"{self.__class__.__name__} (Input shape: {inp_sz})\n"
    res += "=" * n + "\n"
    res += f"{'Layer (type)':<20} {'Output Shape':<20} {'Param #':<10} {'Trainable':<10}\n"
    res += "=" * n + "\n"
    ps,trn_ps = 0,0
    infos = [o for o in infos if o is not None] #see comment in previous cell
    for typ,np,trn,sz in infos:
        if sz is None: continue
        ps += np
        if trn: trn_ps += np
        res += f"{typ:<20} {_print_shapes(sz, bs)[:19]:<20} {np:<10,} {str(trn):<10}\n"
        res += "_" * n + "\n"
    res += f"\nTotal params: {ps:,}\n"
    res += f"Total trainable params: {trn_ps:,}\n"
    res += f"Total non-trainable params: {ps - trn_ps:,}\n\n"
    return Representation(name, inp_shape, out_shape, modules, params, links, xtra), PrettyString(res)

# Cell
@patch
def to_representation(self:Learner):
    "Gets a summary of the model, optimizer and loss function."
    xb = self.dls.train.one_batch()[:self.dls.train.n_inp]
    return self.model.to_representation(*xb)
    res = self.model.summary(*xb)
    res += f"Optimizer used: {self.opt_func}\nLoss function: {self.loss_func}\n\n"
    if self.opt is not None:
        res += f"Model " + ("unfrozen\n\n" if self.opt.frozen_idx==0 else f"frozen up to parameter group number {self.opt.frozen_idx}\n\n")
    res += "Callbacks:\n" + '\n'.join(f"  - {cb}" for cb in sort_by_run(self.cbs))
    return PrettyString(res)

# Cell
@patch
def to_json(self:Representation):
    nodes = list(self.modules)
    links = list(self.links)
    return json.dumps({'nodes':nodes, 'links':links})