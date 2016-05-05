"""A command-line utility which prints the path to pynn_spinnaker_if_curr_dual_exp.
For use by plugins etc to find make files etc.

Installed as "pynn_spinnaker_if_curr_dual_exp_path" by setuptools.
"""

import os.path
from pynn_spinnaker_if_curr_dual_exp import __file__ as f
import sys

def main(args=None):
    print(os.path.dirname(f))
    return 0

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
