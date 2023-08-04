from setuptools import setup

setup(name='psychopy-meg-triggers',
      version='0.1',
      description='MEG triggers for CIMH',
      long_description='MEG triggers for CIMH',
      long_description_content_type="text/markdown",
      url='http://github.com/skjerns/psychopy-MEG-triggers',
      author='skjerns',
      author_email='nomail@nomail.com',
      license='GNU 2.0',
      packages=[],
      install_requires=['PyDAQmx'],
      zip_safe=False,
      classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
      ],)