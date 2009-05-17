## Script (Python) "prefsPasUsersSearch"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=searchstring, findAll
##title=Search for Users in PAS


search_view = context.restrictedTraverse('@@pas_search')

if findAll:
    return search_view.searchUsers(sort_by='userid')
elif searchstring:
    results = search_view.searchUsers(fullname=searchstring) + \
              search_view.searchUsers(login=searchstring)
    return search_view.sort(search_view.merge(results, 'userid'),
                            'userid')
else:
    return []
