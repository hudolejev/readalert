#!/bin/sh -eu

cd ../pub
python3 -m http.server --bind 127.0.0.1
