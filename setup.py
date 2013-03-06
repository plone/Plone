from setuptools import setup, find_packages
import os.path

version = '4.2.5'

setup(name='Plone',
      version=version,
      description="The Plone Content Management System",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "CHANGES.txt")).read(),
      classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Zope2",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        ],
      keywords='Plone CMF python Zope',
      author='Plone Foundation',
      author_email='plone-developers@lists.sourceforge.net',
      url='http://plone.org/',
      license='GPL version 2',
      packages=[],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Products.CMFPlacefulWorkflow',
          'Products.CMFPlone',
          'Products.kupu',
          'plone.app.caching',
          'plone.app.iterate',
          'plone.app.openid',
          'plone.app.theming',
          'wicked',
          # ensure these transient dependencies don't vanish in the 4.2
          # series, just because some libraries get updated and nobody
          # declares the dependency anymore
          'zope.copypastemove',
          'zope.app.component',
          'zope.app.container',
          'zope.app.publisher',
      ],
      )
