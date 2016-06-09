from setuptools import setup, find_packages

setup(
    name="pynn_spinnaker_recurrent_stdp",
    version="0.1",
    packages=find_packages(),
    package_data={'pynn_spinnaker_recurrent_stdp': ['binaries/*.aplx']},

    # Metadata for PyPi
    url="https://github.com/project-rig/pynn_spinnaker_extra_models",
    author="University of Manchester",
    description="Plugin for PyNN SpiNNaker to provide support "
                "for 'Recurrent' STDP synapse type",
    license="GPLv2",
    classifiers=[
        "Development Status :: 3 - Alpha",

        "Intended Audience :: Science/Research",

        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",

        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",

        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",

        "Topic :: Scientific/Engineering",
    ],
    keywords="spinnaker pynn neural simulation",

    # Requirements
    install_requires=["pynn_spinnaker>=0.3"],
    zip_safe=False,  # Partly for performance reasons
)
