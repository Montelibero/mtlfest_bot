#!/bin/bash

cd /home/mtlfest_bot/
source /home/mtlfest_bot/.venv/bin/activate
export ENVIRONMENT=production
python3 main.py mtlfest_bot

deactivate

