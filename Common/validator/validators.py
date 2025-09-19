from django.core.exceptions import ValidationError
from Core.Settings.common import FILE_UPLOAD_MAX_MEMORY_SIZE


def validate_image_extension(image):
    allowed_extensions = ['jpeg', 'jpg', 'png', 'gif']
    extension = image.name.split('.')[-1].lower()

    if extension not in allowed_extensions:
        raise ValidationError(
            'Invalid image format. Please upload a valid image file (JPG, JPEG, PNG, GIF).'
        )


# Calculate the maximum file size in bytes
# e.g 2.5 MB (2.5 * 1024 * 1024 bytes)
# Alternative def name: max_file_size_validator
def validate_max_file_size(value):
    max_size_byte = FILE_UPLOAD_MAX_MEMORY_SIZE
    max_size_mb = max_size_byte / (1024**2)

    print('max_size_mb:', value.size / (1024**2), max_size_mb)
    
    if value.size > max_size_byte:
        raise ValidationError(f'File size cannot exceed {max_size_mb} MB.')
