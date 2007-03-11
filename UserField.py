# -*- coding: utf-8 -*-
#
# File: UserField.py
#
# Copyright (c) 2007 by BlueDynamics Alliance, Austria
# Generator: ArchGenXML Version 1.5.3 dev/svn
#            http://plone.org/products/archgenxml
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

__author__ = """Phil Auersperg <phil@bluedynamics.com>, Peter Holzer <hpeter@agitator.com>,
Jens Klein <jens@bluedynamics.com>"""
__docformat__ = 'plaintext'

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.Field import ObjectField, encode, decode
from Products.Archetypes.Registry import registerField
from Products.Archetypes.utils import DisplayList
from Products.Archetypes import config as atconfig
from Products.Archetypes.Widget import *
from Products.Archetypes.Field  import *
from Products.Archetypes.Schema import Schema
try:
    from Products.generator import i18n
except ImportError:
    from Products.Archetypes.generator import i18n
from Products.UserField import config
from Products.Archetypes.Field import ObjectField
from Products.ATMemberSelectWidget.ATMemberSelectWidget import MemberSelectWidget


##code-section module-header #fill in your manual code here
from sets import Set
import types
from zope.component import ComponentLookupError
from interfaces import IGenericGroupTranslation
##/code-section module-header


class UserField(ObjectField):
    """
    """
    ##code-section class-header #fill in your manual code here
    ##/code-section class-header

    __implements__ = (getattr(ObjectField,'__implements__',()),) + (getattr(ObjectField,'__implements__',()),)


    _properties = ObjectField._properties.copy()
    _properties.update({
        'type': 'userfield',
        'widget': MemberSelectWidget,
        ##code-section field-properties #fill in your manual code here
        'multiValued'     : 0,
        'localrole'       : None,
        'cumulative'      : False,
        'prefill_member'  : False,
        'limitToOwnGroups': True,
        ##/code-section field-properties

        })
        
    security  = ClassSecurityInfo()
    ##code-section security-declarations #fill in your manual code here
    ##/code-section security-declarations

    security.declarePrivate('get')
    security.declarePrivate('getRaw')
    security.declarePrivate('set')

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
            return 'Herrn/Frau %s' % fullname

    def getRaw(self, instance, **kwargs):
        return ObjectField.getRaw(self, instance, **kwargs)

    def set(self, instance, value, **kwargs):
        res = ObjectField.set(self, instance, value, **kwargs)
        if value is None:
            return res

        if type(value) in types.StringTypes:
            users = [value]
        elif type(value) in (types.ListType, types.TupleType):
            users = list(value)
        else:
            raise ValueError, 'only strings and lists/tuples allowed, but you provided the value %s' % value

        if self.localrole is not None:
            localrole = self.localrole
            if type(localrole) in types.StringTypes:
                localrole = [localrole]
            self.setLocalRoles(instance, users, localrole)
        return res

    def get(self, instance, **kwargs):
        return ObjectField.get(self, instance, **kwargs)

    def addLocalRoles(self, instance, member_id,roles=[]):
        pm = instance.portal_membership

        for r in roles:
              self._setLocalRoles(instance, member_ids=[member_id]
                                    , member_role = r,
                                    )
    def _setLocalRoles(self, instance, member_ids, member_roles, reindex=True):
        """Add local roles on an item.
        """
        if type(member_roles) in (type(''),type(u'')):
            member_roles=[member_roles]

        pm = instance.portal_membership

        for member_id in member_ids:
            roles = Set(instance.get_local_roles_for_userid( userid=member_id ))
            roles.union_update(member_roles)
            instance.manage_setLocalRoles( member_id, roles )

        if reindex:
            # It is assumed that all objects have the method
            # reindexObjectSecurity, which is in CMFCatalogAware and
            # thus PortalContent and PortalFolder.
            instance.reindexObjectSecurity()

    def setLocalRoles(self, instance, member_id, roles=[]):
        pm = instance.portal_membership
        if type(roles) in (types.ListType, types.TupleType):
            roles = [roles]

        for role in roles:
            if not self.cumulative:
                self.deleteLocalRolesByRole(instance, role)
            self._setLocalRoles(instance, member_id, role)

    def deleteLocalRolesByRole(self, obj, role, reindex=1, recursive=0):
        """Delete local roles of specified members.
        """

        member_ids = obj.users_with_local_role(role)
        # XXX
        if 1 or _checkPermission(ChangeLocalRoles, obj):
            obj.manage_delLocalRoles([member_ids])
            #for member_id in member_ids:
                #roles = [r for r in obj.get_local_roles_for_userid(userid=member_id)\
                #         if r != role]
                #if roles:
                    #obj.manage_setLocalRoles(member_id, roles)
                #else:
                    #obj.manage_delLocalRoles([member_id])
        
        # if recursive: handle subobjects
        if recursive and hasattr( aq_base(obj), 'contentValues' ):
            for subobj in obj.contentValues():
                self.deleteLocalRolesByRole(subobj, member_ids, 0, 1)

        if reindex:
            # reindexObjectSecurity is always recursive
            obj.reindexObjectSecurity()

    def getDefault(self, instance):
        default = ObjectField.getDefault(self, instance)
        if default:
            return default
        group = self.widget.groupName # we might get a generic group-name here!
        try:
            translator = IGenericGroupTranslation(instance)
        except ComponentLookupError:
            pass
        else:
            group = translator.convertToRealGroup(group)

        if not self.prefill_member:
            return default
        
        member = instance.portal_membership.getAuthenticatedMember()
        if not member:
            return default

        if self.limitToOwnGroups and group and group not in member.getGroups():
            return default

        default = member.getId()
        return default


registerField(UserField,
              title='UserField',
              description='')

##code-section module-footer #fill in your manual code here
##/code-section module-footer



