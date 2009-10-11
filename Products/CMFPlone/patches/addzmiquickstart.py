from App.Common import package_home
from App.Management import Navigation
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

PACKAGE_HOME = package_home(globals())
Navigation.zope_quick_start = PageTemplateFile('quick_start', PACKAGE_HOME)
