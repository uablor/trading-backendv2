from rest_framework import permissions


class IsVerified(permissions.BasePermission):
    """
    Custom permission to only allow verified users to access the view.
    """
    message = 'Please verify your email address...!'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_verify

# class HasAnyPermission(permissions.BasePermission):
#     def __init__(self, required_permissions):
#         self.required_permissions = required_permissions

#     def has_permission(self, request, view):
#         # Check if the user has any of the required permissions
#         return any(request.user.has_perm(permission) for permission in self.required_permissions)

#     def has_object_permission(self, request, view, obj):
#         return self.has_permission(request, view)

class HasAnyPermission(permissions.BasePermission):
    def __init__(self, required_permissions=None):
        self.required_permissions = required_permissions or {}
        
    def group_has_permission(self, request, view):
        pass

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        permissions_required = self.required_permissions.get(request.method, [])
        
        # print(f"Checking permissions: {permissions_required} for user {request.user}")
        # all_user_permissions = list(request.user.get_all_permissions())
        # print(f"all permission of {request.user} : {all_user_permissions}")
        # for permission in permissions_required:
            # print(f"User has permission {permission}: {request.user.has_perm(permission)}")
            
        return any(request.user.has_perm(permission) for permission in permissions_required)

        # print(f"Permission check result: {result}")
        # return result  # เพิ่มคำสั่ง return เพื่อคืนค่าผลลัพธ์
        
        
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
    