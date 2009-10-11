from OFS.ObjectManager import ObjectManager

ADD_PLONE_SITE_HTML = '''
<dtml-if "_.len(this().getPhysicalPath()) == 1">
  <!-- Add Plone site action-->
  <div style="text-align: right; margin-top:0.5em; margin-bottom:0em;
              font-size: 120%; text-decoration: underline;
  ">
  <a href="&dtml-URL1;/?:method=manage_addProduct/CMFPlone/addPloneSiteForm&site_id=Plone"
     target="_top">
    Add Plone Site
  </a></div>
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
