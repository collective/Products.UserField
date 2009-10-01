import types
from sets import Set
from zope.component import ComponentLookupError
from AccessControl import ClassSecurityInfo
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.Registry import registerField
from Products.Archetypes.Field import ObjectField
from Products.UserAndGroupSelectionWidget import UserAndGroupSelectionWidget
from utils import setLocalRoles

class UserField(ObjectField):
    """Field to store userids"""

    __implements__ = (getattr(ObjectField,'__implements__',()),) + (getattr(ObjectField,'__implements__',()),)

    _properties = ObjectField._properties.copy()
    _properties.update({
        'type'              : 'userfield',
        'widget'            : UserAndGroupSelectionWidget,
        'multiValued'       : False, 
        'localrole'         : None,  # set local role for selected users
        'cumulative'        : False, # cumulative local roles?
        'prefill_member'    : False, # prefill with current member
        'limitToOwnGroups'  : True,  # limit prefill to own groups
        })
        
    security  = ClassSecurityInfo()

    security.declarePrivate('get')
    def get(self, instance, **kwargs):
        return ObjectField.get(self, instance, **kwargs)


    security.declarePrivate('getRaw')
    def getRaw(self, instance, **kwargs):
        return ObjectField.getRaw(self, instance, **kwargs)


    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        res = ObjectField.set(self, instance, value, **kwargs)
        if value is None:
            return res

        if isinstance(value, basestring):
            users = [value]
        elif type(value) in (types.ListType, types.TupleType):
            users = list(value)
        else:
            raise ValueError, 'only strings and lists/tuples allowed, but you provided the value %s' % value

        if self.localrole:
            localrole = self.localrole
            if isinstance(localrole, basestring):
                localrole = [localrole]
            setLocalRoles(instance, users, localrole, cumulative=self.cumulative)
        return res


    def getFullName(self, instance, casus=1):
        userid = self.get(instance) or ''
        mt = getToolByName(instance, 'portal_membership')
        userinfo = mt.getMemberInfo(userid)
        if userinfo is None or not userinfo['fullname']:
            return userid
        # BKS special
        fullname = userinfo['fullname'].replace('_', ' ')
        if casus == 1:
            return fullname
        else:
            # superfluos?
            return 'Herrn/Frau %s' % fullname
                                                   
    def getDefault(self, instance):
        default = ObjectField.getDefault(self, instance)
        if default:
            return default
        
        # The field should not know about it's widget. from this point of view
        # this field sucks
        if hasattr(self.widget, 'getGroupId'):
            group = self.widget.getGroupId(instance)
        else:
            group = None

        if not self.prefill_member:
            return default
            
        member = instance.portal_membership.getAuthenticatedMember()
        if not member:
            return default

        if self.limitToOwnGroups and group and group not in member.getGroups():
            return default

        default = member.getId()
        return default


registerField(UserField, title='UserField', description='')

