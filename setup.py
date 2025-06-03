from glob import glob
import os
from setuptools import find_packages, setup

PACKAGE_NAME = 'pihatel_ros2_driver'
SHARE_DIR = os.path.join("share", PACKAGE_NAME)

setup(
    name=PACKAGE_NAME,
    version='1.0.0',
    packages=["libpihatel_ros2_driver", "libpihatel_ros2_driver.nodes"],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + PACKAGE_NAME]),
        ('share/' + PACKAGE_NAME, ['package.xml']),
        (os.path.join(SHARE_DIR, "launch"), glob(os.path.join("launch", "*.launch.py"))),
    ],
    package_dir={'': 'src', },
    install_requires=['setuptools',
                      'pyserial'],
    zip_safe=True,
    maintainer='Artem Paraev',
    maintainer_email='artemparaev.dev@gmail.com',
    description='Package to parse data from Pi Hatel GNSS module and publish GPS messages.',
    license='BSD',
    # tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'pihatel_serial_driver = libpihatel_ros2_driver.nodes.pihatel_serial_driver:main',
        ],
    },
)
