from zope.component import getMultiAdapter
from zope.component import getUtility

from Acquisition import aq_inner
from Products.Five import BrowserView
from Products.CMFCore.interfaces import IActionsTool
from Products.CMFCore.interfaces import IConfigurableWorkflowTool
from Products.CMFCore.interfaces import IPropertiesTool
from Products.CMFCore.interfaces import IURLTool
from Products.CMFPlone.interfaces import IPloneTool
from plone.app.content.browser.tableview import Table
import urllib

class FullReviewListView(BrowserView):

    def revlist(self):
        return self.context.my_worklist()

    def url(self):
        return self.context.absolute_url()+'/full_review_list'

    def review_table(self):
        table = ReviewListTable(self.context, self.request)
        return table.render()

class ReviewListTable(object):
    """   
    The review list table renders the table and its actions.
    """                

    def __init__(self, context, request):
        self.context = context
        self.request = request

        url = self.context.absolute_url()
        view_url = url + '/full_review_list'
        self.table = Table(request, url, view_url, self.items,
                           buttons=self.buttons)

    def render(self):
        return self.table.render()

    @property
    def items(self):
        putils = getUtility(IPloneTool)
        url_tool = getUtility(IURLTool)
        plone_view = getMultiAdapter((self.context, self.request), name=u'plone')
        wtool = getUtility(IConfigurableWorkflowTool)
        portal_properties = getUtility(IPropertiesTool)
        site_properties = portal_properties.site_properties
        
        use_view_action = site_properties.getProperty('typesUseViewActionInListings', ())
        browser_default = self.context.browserDefault()

        results = list()
        for i, obj in enumerate(self.context.my_worklist()):
            if i % 2 == 0:
                table_row_class = "even"
            else:
                table_row_class = "odd"
            
            url = obj.absolute_url()
            path = '/'.join(obj.getPhysicalPath())
            icon = plone_view.getIcon(obj);
            
            type_class = 'contenttype-' + putils.normalizeString(
                obj.portal_type)

            review_state = wtool.getInfoFor( obj, 'review_state', '')

            state_class = 'state-' + putils.normalizeString(review_state)
            relative_url = url_tool.getRelativeContentURL(obj)
            obj_type = obj.portal_type

            modified = plone_view.toLocalizedTime(
                obj.ModificationDate(), long_format=1)
            
            if obj_type in use_view_action:
                view_url = url + '/view'
            elif obj.is_folderish:
                view_url = url + "/folder_contents"              
            else:
                view_url = url

            is_browser_default = len(browser_default[1]) == 1 and (
                obj.id == browser_default[1][0])
                                 
            results.append(dict(
                url = url,
                id  = obj.getId(),
                quoted_id = urllib.quote_plus(obj.getId()),
                path = path,
                title_or_id = obj.pretty_title_or_id(),
                description = obj.Description(),
                obj_type = obj_type,
                size = obj.getObjSize(),
                modified = modified,
                icon = icon.html_tag(),
                type_class = type_class,
                wf_state = review_state,
                state_title = wtool.getTitleForStateOnType(review_state,
                                                           obj_type),
                state_class = state_class,
                is_browser_default = is_browser_default,
                folderish = obj.is_folderish,
                relative_url = relative_url,
                view_url = view_url,
                table_row_class = table_row_class,
                is_expired = self.context.isExpired(obj),
            ))
        return results

    @property
    def show_sort_column(self):
        return False

    def buttons(self):
        buttons = []
        actions_tool = getUtility(IActionsTool)
        button_actions = actions_tool.listActionInfos(object=aq_inner(self.context), categories=('folder_buttons', ))

        # Do not show buttons if there is no data, unless there is data to be
        # pasted
        if False:#not len(self.batch):
            if self.context.cb_dataValid():
                for button in button_actions:
                    if button['id'] == 'paste':
                        return [self.setbuttonclass(button)]
            else:
                return []

        for button in button_actions:
            # Make proper classes for our buttons
            if button['id'] != 'paste' or self.context.cb_dataValid():
                buttons.append(self.setbuttonclass(button))
        return buttons

    def setbuttonclass(self, button):
        if button['id'] == 'paste':
            button['cssclass'] = 'standalone'
        else:
            button['cssclass'] = 'context'
        return button
