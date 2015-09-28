from setuptools import setup
import os.path

version = '5.0'

setup(name='Plone',
      version=version,
      description='The Plone Content Management System',
      long_description=open('README.rst').read() + '\n' +
                       open(os.path.join('docs', 'CHANGES.rst')).read(),
      classifiers=[
        'Environment :: Web Environment',
        'Framework :: Plone',
        'Framework :: Zope2',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
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
          'Products.Archetypes',
          'Products.ATContentTypes >= 2.1.3',
          'Products.CMFPlacefulWorkflow',
          'Products.CMFPlone',
          'plone.app.caching',
          'plone.app.dexterity',
          'plone.app.iterate',
          'plone.app.openid',
          'plone.app.upgrade',
      ],
      )
