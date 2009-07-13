from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from App.class_init import InitializeClass

from Products.CMFCore.ActionInformation import ActionInfo
from Products.CMFCore.TypesTool import TypesTool as BaseTool

from Products.CMFPlone import ToolNames
from Products.CMFPlone.PloneBaseTool import PloneBaseTool


class TypesTool(PloneBaseTool, BaseTool):

    meta_type = ToolNames.TypesTool
    security = ClassSecurityInfo()
    toolicon = 'skins/plone_images/document_icon.gif'

    security.declarePublic('listTypeTitles')
    def listTypeTitles(self, container=None):
        """ Return a dictionary of id/Title combinations """
        typenames = {}
        for t in self.listTypeInfo( container ):
            name = t.getId()
            if name:
                typenames[ name ] = t.title_or_id()

        return typenames

    security.declarePublic('listActionInfos')
    def listActionInfos(self, action_chain=None, object=None,
                        check_visibility=1, check_permissions=1,
                        check_condition=1, max=-1, categories=None):
        # List ActionInfo objects.
        # (method is without docstring to disable publishing)
        #
        actions = self.listActions(object=object)
        if categories is not None:
            result = []
            for action in actions:
                cat = getattr(aq_base(action), 'category', 'folder/add')
                if cat in categories:
                    result.append(action)
            if len(result) == 0:
                return []
            actions = result

        ec = self._getExprContext(object)
        actions = [ ActionInfo(action, ec) for action in actions ]

        if action_chain:
            filtered_actions = []
            if isinstance(action_chain, basestring):
                action_chain = (action_chain,)
            for action_ident in action_chain:
                sep = action_ident.rfind('/')
                category, id = action_ident[:sep], action_ident[sep+1:]
                for ai in actions:
                    if id == ai['id'] and category == ai['category']:
                        filtered_actions.append(ai)
            actions = filtered_actions

        if categories is not None:
            actions = [ai for ai in actions
                          if ai['category'] in categories]

        action_infos = []
        for ai in actions:
            if check_visibility and not ai['visible']:
                continue
            if check_permissions and not ai['allowed']:
                continue
            if check_condition and not ai['available']:
                continue
            action_infos.append(ai)
            if max + 1 and len(action_infos) >= max:
                break
        return action_infos

TypesTool.__doc__ = BaseTool.__doc__

InitializeClass(TypesTool)
