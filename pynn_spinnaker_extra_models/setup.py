from setuptools import setup, find_packages

setup(
    name="pynn_spinnaker_extra_models",
    version="0.1",
    packages=find_packages(),

    # Metadata for PyPi
    url="https://github.com/project-rig/pynn_spinnaker_extra_models",
    author="University of Manchester",
    description="Selection of plugings for PyNN SpiNNaker to provide support for a selection of to be simulated on SpiNNaker",
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
    keywords="spinnaker pynn neural simulation bcpnn",

    # Requirements
    install_requires=["pynn>=0.8", "rig>=1.1.0, <2.0.0",
                      "bitarray>=0.8.1, <1.0.0", "pynn_spinnaker>=0.1"],
    zip_safe=False,  # Partly for performance reasons
)
