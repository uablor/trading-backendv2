from rest_framework import permissions
from Common.permission.basepermission import HasAnyPermission


class UserPermission(HasAnyPermission):
    def __init__(self):
        required_permissions = {
            'GET': ['account.view_user'],
            'POST': ['account.add_user'],
            'PUT': ['account.change_user'],
            'PATCH': ['account.change_user'],
            'DELETE': ['account.delete_user']
        }
        super().__init__(required_permissions)

    # def has_permission(self, request, view):
    #     if request.user.is_superuser:
    #         return True
    #     return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        if obj.is_superuser and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return False
        return super().has_object_permission(request, view, obj)

class GroupPermission(HasAnyPermission):
    def __init__(self):
        required_permissions = {
            'GET': ['auth.view_group'],
            'POST': ['auth.add_group'],
            'PUT': ['auth.change_group'],
            'PATCH': ['auth.change_group'],
            'DELETE': ['auth.delete_group']
        }
        super().__init__(required_permissions)

class PermissionPermission(HasAnyPermission):
    def __init__(self):
        required_permissions = {
            'GET': ['auth.view_permission'],
            'POST': ['auth.add_permission'],
            'PUT': ['auth.change_permission'],
            'PATCH': ['auth.change_permission'],
            'DELETE': ['auth.delete_permission']
        }

        super().__init__(required_permissions)
        
        
# class UserPermission(permissions.BasePermission):

#     def has_permission(self, request, view):
#         if request.user.is_superuser:
#             return True
#         if request.method == "GET":
#             return request.user.groups.filter(permissions__codename="view_user").exists()
#         if request.method == "POST":
#             return request.user.groups.filter(permissions__codename="add_user").exists()
#         if request.method in ["PUT", "PATCH"]:
#             return request.user.groups.filter(permissions__codename="change_user").exists()
#         if request.method == "DELETE":
#             return request.user.groups.filter(permissions__codename="delete_user").exists()
#         return False 


# class GroupPermission(permissions.BasePermission):

#     def has_permission(self, request, view):
#         if request.user.is_superuser:
#             return True
#         if request.method == "GET":
#             return request.user.groups.filter(permissions__codename="view_group").exists()
#         if request.method == "POST":
#             return request.user.groups.filter(permissions__codename="add_group").exists()
#         if request.method in ["PUT", "PATCH"]:
#             return request.user.groups.filter(permissions__codename="change_group").exists()
#         if request.method == "DELETE":
#             return request.user.groups.filter(permissions__codename="delete_group").exists()
#         return False 


# class PermissionPermission(permissions.BasePermission):

#     def has_permission(self, request, view):
#         if request.user.is_superuser:
#             return True
#         if request.method == "GET":
#             return request.user.groups.filter(permissions__codename="view_permission").exists()
#         if request.method == "POST":
#             return request.user.groups.filter(permissions__codename="add_permission").exists()
#         if request.method in ["PUT", "PATCH"]:
#             return request.user.groups.filter(permissions__codename="change_permission").exists()
#         if request.method == "DELETE":
#             return request.user.groups.filter(permissions__codename="delete_permission").exists()
#         return False 