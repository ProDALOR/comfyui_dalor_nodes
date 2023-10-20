import json
from io import BytesIO
import traceback
import base64

from PIL import Image
import numpy as np

from urllib3 import PoolManager


class OurApiSend:

    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                {"images": ("IMAGE", ),
                 "callback_url": ("STRING", {"default": ""}),
                 "id": ("STRING", {"default": ""}),
                 }
                }

    RETURN_TYPES = ()
    FUNCTION = "send_images"

    OUTPUT_NODE = True

    CATEGORY = "image"

    def send_images(self, images, callback_url: str, id: str):
        for image in images:
            img = Image.fromarray(
                np.clip(255. * image.cpu().numpy(), 0, 255).astype(np.uint8)
            )

            bytes_file = BytesIO()

            img.save(bytes_file, format="png")

            bytes_file.seek(0)

            try:

                encoded_body = json.dumps({
                    "id": id,
                    "processed_image": base64.b64encode(bytes_file.getvalue()).decode()
                })

                http = PoolManager()

                http.request(
                    'POST',
                    callback_url,
                    headers={'Content-Type': 'application/json'},
                    body=encoded_body
                )

            except:
                traceback.print_exc()

        return ()
