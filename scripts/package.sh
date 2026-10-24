#!/bin/sh
cd "$(dirname "$0")/.." && zip -r ../nacos-custech-voting.zip . -x ".env" "*/__pycache__/*" ".venv/*" ".pytest_cache/*"
