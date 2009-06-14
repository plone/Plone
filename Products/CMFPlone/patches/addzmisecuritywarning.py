from AccessControl.Role import RoleManager

ADD_SECURITY_WARNING = '''
<!-- Added security warning -->
<p style="font-size:120%; color:red; font-weight:bold;">
Attention!
<br />
Any security settings for Plone objects changed here are liable to be 
overwritten without warning. To assign local roles use the "Sharing" tab in 
Plone. More complex changes should be made using workflows where appropriate.</p>
<!-- End security warning -->
'''

normal = RoleManager._normal_manage_access
orig = normal.read()
pos = orig.find('</dtml-with>')

# Add in our warning at the right position
new = orig[:pos] + ADD_SECURITY_WARNING + orig[pos:]

# Modify the manage_main
normal.edited_source = new
normal._v_cooked = normal.cook()
