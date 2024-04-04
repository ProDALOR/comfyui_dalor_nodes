import os
import ssl
from typing import List, Tuple
import time
import json
from itertools import islice
from io import BytesIO
from dataclasses import dataclass
import traceback

from PIL import Image
import numpy as np
from PIL.PngImagePlugin import PngInfo

from comfy.cli_args import args
import folder_paths

from urllib3 import HTTPSConnectionPool

telegram_host = "api.telegram.org"
default_telegram_timeout = 60


def load_response(resp) -> dict:
    try:
        return json.loads(resp.data)
    except:
        return {}


def batched(iterable, n):
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


def prepare_request(telegram_timeout: float = default_telegram_timeout) -> HTTPSConnectionPool:
    return HTTPSConnectionPool(
        host=telegram_host,
        timeout=telegram_timeout,
        assert_hostname=False,
        assert_fingerprint=False,
        cert_reqs=ssl.CERT_NONE
    )


@dataclass
class BotImage:

    filename: str
    picture: bytes
    file_format: str


def send_picture(bot_token: str, chat_id: str, image: BotImage, as_file: bool = False, telegram_timeout: float = default_telegram_timeout) -> None:
    request = prepare_request(telegram_timeout)
    if not as_file:
        resp = request.request_encode_body(
            method='POST',
            url=f"/bot{bot_token}/sendPhoto",
            fields={
                "chat_id": chat_id,
                "photo": (image.filename, image.picture, image.file_format)
            }
        )
    else:
        resp = request.request_encode_body(
            method='POST',
            url=f"/bot{bot_token}/sendDocument",
            fields={
                "chat_id": chat_id,
                "document": (image.filename, image.picture, image.file_format)
            }
        )
    response = load_response(resp)
    if response.get('ok'):
        return
    else:
        retry_after = response.get('parameters', {}).get('retry_after', 0)
        if retry_after:
            time.sleep(retry_after)
            send_picture(bot_token, chat_id, image, as_file, telegram_timeout)


def media_item(image: BotImage, as_file: bool = False) -> dict:
    return {"type": "document" if as_file else "photo", "media": f"attach://{image.filename}"}


def multipart_item(image: BotImage) -> Tuple[str, tuple]:
    return (image.filename, (image.filename, image.picture, image.file_format))


def send_pictures_group(bot_token: str, chat_id: str, images: List[BotImage], as_file: bool = False, telegram_timeout: float = default_telegram_timeout) -> None:
    request = prepare_request(telegram_timeout)
    resp = request.request_encode_body(
        method='POST',
        url=f"/bot{bot_token}/sendMediaGroup",
        fields={
            "chat_id": chat_id,
            "media": json.dumps(list(map(lambda i: media_item(i, as_file=as_file), images))),
            **dict(map(multipart_item, images))
        }
    )
    response = load_response(resp)
    if response.get('ok'):
        return
    else:
        retry_after = response.get('parameters', {}).get('retry_after', 0)
        if retry_after:
            time.sleep(retry_after)
            send_pictures_group(bot_token, chat_id, images,
                                as_file, telegram_timeout)


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
                 "send_object": (["as_photo", "as_document"],),
                 "send_count": (["by_one", "by_groups"],),
                 "filename_prefix": ("STRING", {"default": "ComfyUITG"})},
                "telegram_timeout": ("FLOAT", {"default": default_telegram_timeout}),
                "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
                }

    RETURN_TYPES = ()
    FUNCTION = "send_images"

    OUTPUT_NODE = True

    CATEGORY = "image"

    def send_images(self, images, bot_token: str, chat_id: str, send_object: str, send_count: str, filename_prefix: str = "ComfyUITG", telegram_timeout: float = default_telegram_timeout, prompt=None, extra_pnginfo=None):

        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])

        results = list()
        bot_results = list()

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

            bot_results.append(BotImage(
                filename=file,
                picture=bytes_file.getvalue(),
                file_format="image/png"
            ))

            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })

            counter += 1

        if bot_results:

            if len(bot_results) == 1 or send_count != "by_groups":
                for bot_res in bot_results:
                    try:
                        send_picture(bot_token, chat_id, bot_res,
                                     send_object == "as_document", telegram_timeout)
                    except:
                        traceback.print_exc()
            else:
                for bot_res in batched(bot_results, 10):
                    try:
                        send_pictures_group(
                            bot_token, chat_id, bot_res,
                            send_object == "as_document", telegram_timeout)
                    except:
                        traceback.print_exc()

        return {"ui": {"images": results}}


NODE_CLASS_MAPPINGS = {
    "TelegramSend": TelegramSend
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TelegramSend": "Send to telegram"
}
