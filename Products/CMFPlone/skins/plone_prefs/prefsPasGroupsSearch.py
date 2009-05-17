## Script (Python) "prefsPasGroupsSearch"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=searchstring, findAll
##title=Search for Groups in PAS


search_view = context.restrictedTraverse('@@pas_search')

if findAll:
    return search_view.searchGroups(sort_by='id')
elif searchstring:
    results = search_view.searchGroups(id=searchstring) + \
              search_view.searchGroups(title=searchstring)
    return search_view.sort(search_view.merge(results, 'id'),
                            'id')
else:
    return []
