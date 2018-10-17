import setuptools

setuptools.setup(
    name="bee-experiment",
    version="0.1.0",
    author="Paul",
    packages=[
        "bee_launcher",
        "bee_monitor",
        "bee_logging",
        "bee_internal",
        "bee_orchestrator",
    ],
    include_package_date=False,
    url="https://github.com/paulbry/BeeExperiment",
    description="BeeExperiment",
    install_requires=[
        'termcolor',
        'PyYAML',
        'Pyro4'
    ],
    entry_points={
        'console_scripts': [
            'bee-launcher = bee_launcher.__main__:main',
            'bee-orchestrator = bee_orchestrator.__main__:main',
            'bee-monitor = bee_monitor.__main__:main'
        ]
    }
)
