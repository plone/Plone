from OFS.ObjectManager import ObjectManager

ADD_PLONE_SITE_HTML = '''
<dtml-if "_.len(this().getPhysicalPath()) == 1">
  <!-- Add Plone site action-->
  <form method="get" 
        action="&dtml-URL1;/@@plone-addsite"
        style="text-align: right; margin-top:0.5em; margin-bottom:0em;"
        target="_top">
    <input type="hidden" name="site_id" value="Plone" />
    <input type="submit" value="Add Plone Site" />
  </form>
</dtml-if>
'''

main = ObjectManager.manage_main
orig = main.read()
pos = orig.find('<!-- Add object widget -->')

# Add in our button html at the right position
new = orig[:pos] + ADD_PLONE_SITE_HTML + orig[pos:]

# Modify the manage_main
main.edited_source = new
main._v_cooked = main.cook()
