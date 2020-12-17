# coding: utf-8
#
# Copyright 2011 Yesudeep Mangalapilly <yesudeep@gmail.com>
# Copyright 2012 Google, Inc & contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import importlib.util
import sys
import os
import os.path
from platform import machine
from setuptools import setup, find_packages
from setuptools.extension import Extension
from setuptools.command.build_ext import build_ext


# Because this library provides extension modules for macOS, but not for other
# platforms, we want to provide built distributions for each macOS platform, but we
# explicitly DON'T want to provide a cross-platform pure-Python wheel to fall back on.
#
# This is because in the event that a new Python version is released or a new
# macOS platform is released, macOS users won't be able to install the built
# distributions we've provided and should fall back to the source distribution,
# but pip's behavior is to prefer a pure-Python wheel first, which will be
# missing the extension modules.
#
# However, to provide built distributions for Linux and Windows (which don't
# have extension modules) we can just build a pure-Python wheel on that
# platform and override the platform name manually via wheel's --plat-name
# feature, to provide a platform-specific wheel.
#
# Since this is fairly uncommon, and because we are not invoking wheel
# directly, we do this by overriding the bdist_wheel command to set
# `--plat-name` at build time.
try:
    from wheel.bdist_wheel import get_platform, bdist_wheel as _bdist_wheel

    class bdist_wheel(_bdist_wheel):
        def finalize_options(self):
            # Call the original function first
            _bdist_wheel.finalize_options(self)

            # Get the current platform name that we're building on
            plat_name = get_platform(None)

            # Rewrite the platform name if necessary
            if plat_name.startswith("macosx"):
                # We're building for macosx, which is actually platform-specific
                pass
            elif plat_name.startswith("linux"):
                # This is a pure Python wheel that will work on any Linux platform
                self.plat_name_supplied = True
                self.plat_name = "manylinux2014"
            else:
                # This is a pure Python wheel that will work on any Windows platform
                self.plat_name_supplied = True
                self.plat_name = plat_name


except ImportError:
    # Same behavior as if wheel is not installed in the buid environment
    bdist_wheel = None


SRC_DIR = 'src'
WATCHDOG_PKG_DIR = os.path.join(SRC_DIR, 'watchdog')

# Load the module version
spec = importlib.util.spec_from_file_location(
    'version', os.path.join(WATCHDOG_PKG_DIR, 'version.py'))
version = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version)

# Ignored Apple devices on which compiling watchdog_fsevents.c would fail.
# The FORCE_MACOS_MACHINE envar, when set to 1, will force the compilation.
_apple_devices = ('appletv', 'iphone', 'ipod', 'ipad', 'watch')
is_macos = sys.platform == 'darwin' and not machine().lower().startswith(_apple_devices)

ext_modules = []
if is_macos or os.getenv('FORCE_MACOS_MACHINE', '0') == '1':
    ext_modules = [
        Extension(
            name='_watchdog_fsevents',
            sources=[
                'src/watchdog_fsevents.c',
            ],
            libraries=['m'],
            define_macros=[
                ('WATCHDOG_VERSION_STRING',
                 '"' + version.VERSION_STRING + '"'),
                ('WATCHDOG_VERSION_MAJOR', version.VERSION_MAJOR),
                ('WATCHDOG_VERSION_MINOR', version.VERSION_MINOR),
                ('WATCHDOG_VERSION_BUILD', version.VERSION_BUILD),
            ],
            extra_link_args=[
                '-framework', 'CoreFoundation',
                '-framework', 'CoreServices',
            ],
            extra_compile_args=[
                '-std=c99',
                '-pedantic',
                '-Wall',
                '-Wextra',
                '-fPIC',

                # Issue #620
                '-Wno-nullability-completeness',
                # Issue #628
                '-Wno-nullability-extension',
                '-Wno-newline-eof',

                # required w/Xcode 5.1+ and above because of '-mno-fused-madd'
                '-Wno-error=unused-command-line-argument'
            ]
        ),
    ]

extras_require = {
    'watchmedo': ['PyYAML>=3.10', 'argh>=0.24.1'],
}

with open('README.rst', encoding='utf-8') as f:
    readme = f.read()

with open('changelog.rst', encoding='utf-8') as f:
    changelog = f.read()

setup(name="watchdog",
      version=version.VERSION_STRING,
      description="Filesystem events monitoring",
      long_description=readme + '\n\n' + changelog,
      author="Yesudeep Mangalapilly",
      author_email="yesudeep@gmail.com",
      license="Apache License 2.0",
      url="http://github.com/gorakhargosh/watchdog",
      keywords=' '.join([
          'python',
          'filesystem',
          'monitoring',
          'monitor',
          'FSEvents',
          'kqueue',
          'inotify',
          'ReadDirectoryChangesW',
          'polling',
          'DirectorySnapshot',
      ]),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Apache Software License',
          'Natural Language :: English',
          'Operating System :: POSIX :: Linux',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: POSIX :: BSD',
          'Operating System :: Microsoft :: Windows :: Windows Vista',
          'Operating System :: Microsoft :: Windows :: Windows 7',
          'Operating System :: Microsoft :: Windows :: Windows 8',
          'Operating System :: Microsoft :: Windows :: Windows 8.1',
          'Operating System :: Microsoft :: Windows :: Windows 10',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3 :: Only',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: Implementation :: PyPy',
          'Programming Language :: C',
          'Topic :: Software Development :: Libraries',
          'Topic :: System :: Monitoring',
          'Topic :: System :: Filesystems',
          'Topic :: Utilities',
      ],
      package_dir={'': SRC_DIR},
      packages=find_packages(SRC_DIR),
      include_package_data=True,
      extras_require=extras_require,
      cmdclass={
          'build_ext': build_ext,
          'bdist_wheel': bdist_wheel,
      },
      ext_modules=ext_modules,
      entry_points={'console_scripts': [
          'watchmedo = watchdog.watchmedo:main [watchmedo]',
      ]},
      python_requires='>=3.6',
      zip_safe=False
)
