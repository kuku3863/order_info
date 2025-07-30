from .models import Permission

def inject_permissions():
    return dict(Permission=Permission)