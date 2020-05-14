# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/01_explorer.ipynb (unless otherwise specified).

__all__ = ['logger', 'Events', 'clientEvents', 'serverEvents', 'FastExplorer', 'header_data_from_array_1_0',
           'get_numpy_bytes', 'load_input', 'get_heatmap']

# Cell
from fastai2.vision.all import *
from .representation import *
from starlette.applications import Starlette
from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocketDisconnect
import uvicorn, asyncio, json, logging
import nest_asyncio
nest_asyncio.apply()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Cell
class Events:
    def __init__(self, d):
        for k,v in d.items(): setattr(self, k, v)

    def __repr__(self):
        d = '\n'.join([f'  {k}: {v}' for k,v in self.__dict__.items()])
        res = f'{self.__class__.__name__} (\n{d}\n)'
        return res

clientEvents = Events({
    'SEND_DATA': 'socket/socketReceiveData',
    'INVALID_EVENT': 'socket/socketInvalidEvent',
    'SEND_IMAGE_INPUT': 'socket/socketReceiveImageInput',
    'NOIMAGE_HEATMAP': 'socket/socketNoImageHeatmap',
    'SEND_HEATMAP': 'socket/socketReceiveHeatmap',
    'SEND_ERROR' : 'socket/socketError',
    'CLOSE_CLIENT': 'socket/socketServerClosed',
})

serverEvents = Events({
    'RECEIVE_EVENT': 'socket/sendEvent',
})

# Cell
class FastExplorer:
    'Wrapper around `Representation` and `ProxyServer`.'
    def __init__(self, learn, host='0.0.0.0', port=8000):
        store_attr(self, 'learn,host,port')
        self.representation = learn.to_representation()
        self.denorm = next((func.decodes for func in learn.dls.after_batch if type(func)==Normalize),noop)
        self.server = Starlette()
        self.endpoint = self.server.websocket_route('/ws')(self.endpoint)
        self.socket = None
        self.cache = {'idx':-1, 'hook_layers':[]}

    def __repr__(self): return f'{self.__class__.__name__} ()'

    async def handle_web_client(self, websocket):
        while True:
            try:
                msg = await websocket.receive_json()
                logging.info(f'Client msg: {msg}')
                await self.dispatch_event(websocket, msg)
            except json.JSONDecodeError: logging.info('Invalid JSON received')
            except WebSocketDisconnect: break

    async def dispatch_event(self, websocket, msg):
        typ = msg['type']
        event = msg['payload']['event'].lower()

        if typ != serverEvents.RECEIVE_EVENT:
            logging.info(f'Invalid type: {typ!r}')
        else:
            if hasattr(self, event):
                logging.info(f'Launching: {event}')
                await getattr(self, event)(websocket, msg['payload'])
            else:
                logging.info(f'Invalid event: {event!r}')
                await websocket.send_json({
                    'type': clientEvents.INVALID_EVENT,
                    'payload': {'type': typ}
                })

    async def endpoint(self, websocket):
        # Open socket
        await websocket.accept()
        msg = await websocket.receive_json()
        self.socket = websocket
        logging.info(f'Client connected: {msg}')

        # Manage requests
        await websocket.send_json({
                'type': clientEvents.SEND_DATA,
                'payload': { 'data': self.representation.to_json()}
            })
        await self.handle_web_client(websocket)

        # Close socket
        await self.close_client(websocket, 'Finalized by server')
        logging.info(f'Client closed: {msg}')

    async def close_client(self, websocket, msg):
        await websocket.send_json({
            'type': clientEvents.CLOSE_CLIENT,
            'payload': {'msg': msg}
        })
        await websocket.close()

    def serve(self):
        logging.info(f'To visualize the model information, go to:')
        logging.info(f'https://renato145.github.io/fastexplorer-js')
        uvicorn.run(self.server, host=self.host, port=self.port)


# Cell
@patch
@delegates(FastExplorer.__init__)
def fastexplorer(self:Learner, reload=False, **kwargs):
    if (not hasattr(self, 'explorer')) or reload: self.explorer = FastExplorer(self, **kwargs)
    self.explorer.serve()

# Cell
def header_data_from_array_1_0(array):
    d = {'shape': array.shape}
    if array.flags.c_contiguous  : d['fortran_order'] = False
    elif array.flags.f_contiguous: d['fortran_order'] = True
    else                         : d['fortran_order'] = False

    d['descr'] = np.lib.format.dtype_to_descr(array.dtype)
    return d

def _format_dict(d):
    header = ["{"]
    for key, value in sorted(d.items()):
        # Need to use repr here, since we eval these when reading
        header.append("'%s': %s, " % (key, repr(value)))
    header.append("}")
    return "".join(header)

def _write_array_header(d, version=None):
    header = _format_dict(d)
    header = np.lib.format._filter_header(header)
    if version is None:
        header = np.lib.format._wrap_header_guess_version(header)
    else:
        header = np.lib.format._wrap_header(header, version)
    return header

def get_numpy_bytes(x, typ, xtra=None):
    "Transforms a numpy array into bytes and attach a `clientEvents`"
    a = {'type': typ}
    if xtra is not None: a.update(xtra)
    a = _format_dict(a).encode('latin1')
    a = a + b' '*(128-len(a))
    b = _write_array_header(header_data_from_array_1_0(x))
    c = x.tobytes()
    return a+b+c

# Cell
def _get_children(m, name):
    for n,m in m.named_children():
        if n==name: return m

    raise Exception(f'{name!r} not found in {m}')

def _get_module_path(m, path):
    for p in path.split('/'): m = _get_children(m, p)
    return m

# Cell
@patch
def _get_batch(self:FastExplorer):
    "Load and cache a batch."
    if 'batch' in self.cache.keys(): return self.cache['batch']
    xb,yb = self.learn.dls.valid.one_batch()
    xb_denorm = self.denorm(xb)
    self.cache['batch'] = {'x': xb, 'y': yb, 'xb_denorm': xb_denorm}
    return self.cache['batch']

@patch
def _get_input_sample(self:FastExplorer):
    "Load and cache a sample."
    idx = self.cache['idx']
    x = self._get_batch()['x'][idx,None]
    return x

@patch
def _get_input_image(self:FastExplorer):
    "Load and cache a sample."
    idx = self.cache['idx']
    x = self._get_batch()['xb_denorm'][idx].cpu().contiguous().numpy()
    return x

# Cell
@patch
async def load_input(self:FastExplorer, websocket, payload=None):
    "Sends a data sample to the client."
    self.cache['idx'] = (self.cache['idx'] + 1) % self.learn.dls.bs
    x = self._get_input_image()
    array_bytes = get_numpy_bytes(x, clientEvents.SEND_IMAGE_INPUT)
    await websocket.send_bytes(array_bytes)
    await self._refresh_heatmaps(websocket)

@patch
async def _refresh_input(self:FastExplorer, websocket):
    if self.cache['idx'] == -1: await self.load_input(websocket)

# Cell
@patch
async def get_heatmap(self:FastExplorer, websocket, payload):
    "Sends the heatmap for a particular layer."
    try:
        await self._refresh_input(websocket)
        path = payload.get('path')
#         if path not in self.cache['hook_layers']: self.cache['hook_layers'].append(path)
        if len(self.cache['hook_layers']) == 0: self.cache['hook_layers'].append(path)
        else                                  : self.cache['hook_layers'][0] = path
        layer = _get_module_path(self.learn.model, path)
        x = self._get_input_sample()
        with torch.no_grad(), hook_output(layer) as hook: self.learn.model.eval()(x.cuda())
        hm = hook.stored[0].mean(0).squeeze()
        if hm.ndim < 2:
            await websocket.send_json({'type': clientEvents.NOIMAGE_HEATMAP, 'payload': {'path': path}})
        else:
            hm = hm - hm.min()
            hm = (hm / hm.max()).cpu().numpy()
            array_bytes = get_numpy_bytes(hm, clientEvents.SEND_HEATMAP, xtra={'path': path})
            await websocket.send_bytes(array_bytes)
    except Exception as e:
        await websocket.send_json({'type': clientEvents.SEND_ERROR,
                                   'payload': {'msg': 'Error getting heatmap.'}})

@patch
async def _refresh_heatmaps(self:FastExplorer, websocket):
    for path in self.cache['hook_layers']: await self.get_heatmap(websocket, payload={'path': path})