import os
import json
from io import BytesIO

from PIL import Image
import numpy as np
from PIL.PngImagePlugin import PngInfo

from comfy.cli_args import args
import folder_paths

from urllib3 import HTTPSConnectionPool

telegram_host = "api.telegram.org"


def send_picture(bot_token: str, chat_id: str, filename: str, picture: bytes, file_format: str) -> None:
    request = HTTPSConnectionPool(host=telegram_host, timeout=10)
    request.request_encode_body(
        method='POST',
        url=f"/bot{bot_token}/sendPhoto",
        fields={
            "chat_id": chat_id,
            "photo": (filename, picture, file_format)
        }
    )


class TelegramSend:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""

    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                {"images": ("IMAGE", ),
                 "bot_token": ("STRING", {"default": ""}),
                 "chat_id": ("STRING", {"default": ""}),
                 "filename_prefix": ("STRING", {"default": "ComfyUITG"})},
                "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
                }

    RETURN_TYPES = ()
    FUNCTION = "send_images"

    OUTPUT_NODE = True

    CATEGORY = "image"

    def send_images(self, images, bot_token, chat_id, filename_prefix="ComfyUITG", prompt=None, extra_pnginfo=None):
        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])
        results = list()
        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            metadata = None
            if not args.disable_metadata:
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            file = f"{filename}_{counter:05}_.png"

            bytes_file = BytesIO()

            img.save(bytes_file, format="png", pnginfo=metadata)

            bytes_file.seek(0)

            with open(os.path.join(full_output_folder, file), "wb") as f:
                f.write(bytes_file.getbuffer())

            try:
                send_picture(bot_token, chat_id, file,
                             bytes_file.getvalue(), "image/png")
            except:
                print('Send TG error')

            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })
            counter += 1

        return {"ui": {"images": results}}


NODE_CLASS_MAPPINGS = {
    "TelegramSend": TelegramSend
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TelegramSend": "Send to telegram"
}
