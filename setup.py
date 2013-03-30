
from distutils.core import setup

setup(name='ponypy',
      version='0.1',
      description='Python implementation of Ponyca client/server.',
      author='Valentin Lorentz',
      author_email='progval+ponypy@progval.net',
      url='https://github.com/ProgVal/Ponypy',
      packages=['ponypy', 'ponypy.client', 'ponypy.common', 'ponypy.server'],
      package_data={'ponypy.common': ['opcodes.yml']},
      )
     
