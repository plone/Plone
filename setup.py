from setuptools import setup
import os.path

version = '4.4a1.dev0'

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
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 2 :: Only",
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
          'plone.app.event[archetypes, dexterity]',
          'plone.app.caching',
          'plone.app.contenttypes',
          'plone.app.dexterity',
          'plone.app.iterate',
          'plone.app.openid',
          'plone.app.theming',
          'wicked',
      ],
      )
