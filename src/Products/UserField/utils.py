import types
from Acquisition import aq_base

def takeRoleFromAllCurrentSet(obj, role, reindex=1, recursive=0):
    """Take all from all current on obj set local roles the given role."""
    userids = obj.users_with_local_role(role)
    for uid in userids:
        currentroles = obj.get_local_roles_for_userid(userid=uid)
        filteredroles = [cur for cur in currentroles if cur != role]
        #print "delete local roles for %s" % uid ,
        obj.manage_delLocalRoles([uid])
        if filteredroles:                
            #print "but preserve roles %s" % filteredroles
            obj.manage_setLocalRoles(uid, filteredroles)
    # if recursive: handle subobjects
    if recursive and hasattr( aq_base(obj), 'contentValues' ):
        for subobj in obj.contentValues():
            takeRoleFromAllCurrentSet(subobj, role, 0, 1)
    if reindex:
        # reindexObjectSecurity is always recursive
        obj.reindexObjectSecurity()

def setLocalRoles(instance, userids, roles=[], cumulative=False):
    """Sets local roles on instance."""
    if not roles: 
        return
    if type(roles) not in (types.ListType, types.TupleType):
        roles = [roles]
    if not cumulative:
        for role in roles:
            takeRoleFromAllCurrentSet(instance, role, reindex=0)
    for uid in userids:
        #print ": add local roles %s for users %s" % (roles, uid)
        instance.manage_addLocalRoles(uid, roles)
        
    # It is assumed that all objects have the method
    # reindexObjectSecurity, which is in CMFCatalogAware and
    # thus PortalContent and PortalFolder.
    instance.reindexObjectSecurity()
            
