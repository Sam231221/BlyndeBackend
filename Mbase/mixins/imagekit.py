from django.conf import settings
import base64
import imagekitio
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions

imagekit = imagekitio.ImageKit(
    private_key=settings.IMAGEKIT["PRIVATE_KEY"],
    public_key=settings.IMAGEKIT["PUBLIC_KEY"],
    url_endpoint=settings.IMAGEKIT["URL_ENDPOINT"],
)


class ImageKitMixin:
    def _upload_to_imagekit(self, image_file, folder):
        file_binary = image_file.read()
        file_base64 = base64.b64encode(file_binary).decode("utf-8")
        response = imagekit.upload_file(
            file=file_base64,
            file_name=image_file.name,
            options=UploadFileRequestOptions(
                use_unique_file_name=False,
                folder=folder,
            ),
        )
        return response

    def _delete_imagekit_file(self, file_id):
        try:
            imagekit.delete_file(file_id)
        except Exception as e:
            print(f"Error deleting file from ImageKit: {e}")
