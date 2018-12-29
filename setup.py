from setuptools import setup
import os.path

version = '5.2a2'

setup(
    name='Plone',
    version=version,
    description='The Plone Content Management System',
    long_description=(open('README.rst').read() + '\n' +
                      open(os.path.join('docs', 'CHANGES.rst')).read()),
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Plone',
        'Framework :: Plone :: 5.2',
        'Framework :: Zope',
        'Framework :: Zope :: 4',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    keywords='Plone CMF Python Zope CMS',
    author='Plone Foundation',
    author_email='plone-developers@lists.sourceforge.net',
    url='http://plone.org/',
    license='GPL version 2',
    packages=[],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'plone.app.caching',
        'plone.app.dexterity',
        'plone.app.iterate',
        'plone.app.upgrade',
        'Products.CMFPlacefulWorkflow',
        'Products.CMFPlone',
        'setuptools>=36.2',
    ],
    extras_require={
        'archetypes': [
            'Products.ATContentTypes ; python_version<"3"',
            'archetypes.multilingual ; python_version<"3"',
            'plone.app.contenttypes[archetypes,atrefs] ; python_version<"3"',
        ],
    },
)
