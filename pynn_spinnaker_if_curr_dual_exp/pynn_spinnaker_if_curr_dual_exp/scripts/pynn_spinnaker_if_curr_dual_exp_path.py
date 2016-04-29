"""A command-line utility which prints the path to pynn_spinnaker_if_curr_dual_exp.
For use by plugins etc to find make files etc.

Installed as "pynn_spinnaker_if_curr_dual_exp_path" by setuptools.
"""

import os.path
import pynn_spinnaker_if_curr_dual_exp
import sys

def main(args=None):
    print(os.path.dirname(pynn_spinnaker_if_curr_dual_exp.__file__))
    return 0

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
