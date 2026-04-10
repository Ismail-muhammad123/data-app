from admin_api.models import AdminActionLog

def log_admin_action(user, action_type, description, target=None, metadata=None):
    """
    Helper to create an AdminActionLog entry.
    """
    target_model = None
    target_id = None
    
    if target:
        target_model = target.__class__.__name__
        target_id = str(target.pk) if hasattr(target, 'pk') else str(target)

    return AdminActionLog.objects.create(
        admin_user=user,
        action_type=action_type,
        target_model=target_model,
        target_id=target_id,
        description=description,
        metadata=metadata
    )
