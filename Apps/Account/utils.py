from datetime import datetime
import os


def profile_image_storage(instance, filename):
    profile_id = instance.id

    if profile_id is None:
        # If the Pofile is new and doesn't have an ID yet, use a temporary identifier
        profile_id = "new"

    ext = filename.split('.')[-1]
    current_date = datetime.now().strftime('%d-%m-%Y')
    new_filename = f'profile_{profile_id}_image_{current_date}.{ext}'

    return os.path.join('profile_images/', new_filename)
