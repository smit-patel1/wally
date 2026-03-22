from setuptools import setup
import os
from glob import glob

package_name = 'wally_perception'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='wally',
    maintainer_email='wally@todo.todo',
    description='Wally perception subsystem',
    license='MIT',
    entry_points={
        'console_scripts': [
            'mask_converter_node = wally_perception.mask_converter_node:main',
        ],
    },
)