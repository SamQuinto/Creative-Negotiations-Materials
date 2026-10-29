#!/usr/bin/env python3
"""Score an Empirica offer with the current tested NOVA architecture."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'app'))
from empirica_bridge import main

if __name__=='__main__':
    raise SystemExit(main())
