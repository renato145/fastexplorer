# Fast Explorer
> Work in progress


A utility to visualize models.

Main idea:
* Use this library to attach a learner and initialize a proxy server.
* Connect a javascript client via [fastexplorer-js](https://github.com/renato145/fastexplorer-js).
* Send back and forth relevant information to be visualized.

This will allow to use tools like d3, react and threejs to visualize NN information.

## Install

`pip install git+https://github.com/renato145/fastexplorer.git`

## How to use

Load you Learner as usual and import fastexplorer:

```python
from fastai2.vision.all import *
from fastexplorer.all import *

path = untar_data(URLs.PETS)
files = get_image_files(path/"images")
def label_func(f): return f[0].isupper()
dls = ImageDataLoaders.from_name_func(path, files, label_func, item_tfms=Resize(224))
learn = cnn_learner(dls, resnet34)
```

When ready, start serving the server:

```python
#srv
learn.fastexplorer(True)
```

    INFO:     Started server process [25269]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
    INFO:     Shutting down
    INFO:     Waiting for application shutdown.
    INFO:     Application shutdown complete.
    INFO:     Finished server process [25269]


Finally, go to [https://renato145.github.io/fastexplorer-js/]() to visualize the model:
![](nbs/images/js_preview.png)
