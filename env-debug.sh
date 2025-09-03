#!/bin/bash
source venv/bin/activate
python -c "from main import load_config; import pprint; pprint.pprint(load_config())"