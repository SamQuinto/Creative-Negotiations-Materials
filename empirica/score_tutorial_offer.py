#!/usr/bin/env python3
"""Score a tutorial offer with the current general-purpose A1 by default."""

from __future__ import annotations

from score_offer import main


if __name__ == "__main__":
    # Keep tutorial selection local to this call; do not change a server's defaults.
    raise SystemExit(main(default_space="tutorial"))
