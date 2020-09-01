#!/usr/bin/env bash

set -euf -o pipefail

# Replace tabs with spaces
python << END
from glob import glob

for file in glob("footbot/**/*.py"):
    before = open(file).read()
    open(file, 'w').write(before.replace('\t', ' '*4))
END

# Sort imports and split to single lines
isort -sl -rc -p footbot footbot/ tests/

# Format
black -q -t py38 footbot/ tests/

# Lint
flake8 --max-line-length 100 footbot
