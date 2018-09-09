import setuptools

setuptools.setup(
    name="bee-combs",
    version="0.1.0",
    license="https://github.com/lanl/BEE/blob/master/LICENSE",
    author="Paul",
    packages=[
        "bee_charliecloud"
    ],
    include_package_data=False,
    url="https://github.com/paulbry/BEE",
    description="BEE: Build and Execute Environment",
    install_requires=[
        # none atm
    ],
    entry_points={
        'console_scripts': [
            # none atm
        ]
    }
)
