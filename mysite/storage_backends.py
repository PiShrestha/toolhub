from storages.backends.s3boto3 import S3Boto3Storage

# this file allows Django to handle file storage with cloud providers instead of using the local file system.

class StaticStorage(S3Boto3Storage):
    location = 'static'
    default_acl = None

class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    default_acl = None