# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/01_explorer.ipynb (unless otherwise specified).

__all__ = ['logger', 'FastExplorer', 'close_client']

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
class FastExplorer:
    'Wrapper around `Representation` and `ProxyServer`.'
    def __init__(self, learn, host='0.0.0.0', port=8000):
        store_attr(self, 'learn,host,port')
        self.representation = learn.to_representation()
        self.server = Starlette()
        self.endpoint = self.server.websocket_route('/ws')(self.endpoint)
        self.socket = None

    def __repr__(self): return f'{self.__class__.__name__} ()'

    async def endpoint(self, websocket):
        # Open socket
        await websocket.accept()
        msg = await websocket.receive_json()
        self.socket = websocket
        logging.info(f'Client connected: {msg}')

        # Manage requests
        await websocket.send_json({'event': 'representation_data', 'msg': self.representation.to_json()})

        # Close socket
#         state[client_type] = False
#         websocket_dict.pop(client_type)
        await close_client(websocket, 'Finalized by server')
        logging.info(f'Client closed: {msg}')

    def serve(self): uvicorn.run(self.server, host=self.host, port=self.port)

# Cell
async def close_client(websocket, msg):
    await websocket.send_json({'event': 'close', 'msg': msg})
    await websocket.close()

# Cell
@patch
@delegates(FastExplorer.__init__)
def fastexplorer(self:Learner, **kwargs):
    if not hasattr(self, 'explorer'): self.explorer = FastExplorer(self, **kwargs)
    self.explorer = FastExplorer(self, **kwargs)
    self.explorer.serve()