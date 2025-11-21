#!/usr/bin/python
# -*- coding: utf-8 -*-
print("module [app] loaded")
import os

from backend import app


if __name__ == "__main__":
    port = int(os.environ.get('PORT', app.config['BIND_PORT']))
    app.run("0.0.0.0", debug=True, port=port, threaded=True)