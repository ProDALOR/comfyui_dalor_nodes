from typing import Iterable
import numpy as np
from PIL import Image

import torch
import torch.nn as nn
from transformers import SegformerImageProcessor, AutoModelForSemanticSegmentation

category = 'segformer with image'


class SegformerImageWithSemantic:

    @classmethod
    def INPUT_TYPES(self):
        return {"required":
                {
                    "image": ("IMAGE",)
                }
                }

    RETURN_TYPES = ("SEGFORMER_LAYERS",)
    RETURN_NAMES = ("segformer_layers",)

    FUNCTION = "image_to_layers"

    CATEGORY = category

    def image_to_layers(self, image: Iterable[torch.Tensor]):

        processor = SegformerImageProcessor.from_pretrained(
            "mattmdjaga/segformer_b2_clothes")
        model = AutoModelForSemanticSegmentation.from_pretrained(
            "mattmdjaga/segformer_b2_clothes")

        for image_ in image:

            np_data = np.clip(
                255. * image_.squeeze().cpu().numpy(), 0, 255).astype(np.uint8)

            img = Image.fromarray(np_data)

            inputs = processor(images=img, return_tensors="pt")

            outputs = model(**inputs)
            logits = outputs.logits.cpu()

            upsampled_logits = nn.functional.interpolate(
                logits,
                size=img.size[::-1],
                mode="bilinear",
                align_corners=False,
            )

            pred_seg = upsampled_logits.argmax(dim=1)[0]

            return (pred_seg.squeeze().cpu().numpy(), )


class SegformerImageChooseLayer:

    @classmethod
    def INPUT_TYPES(self):
        return {"required":
                {
                    "segformer_layers": ("SEGFORMER_LAYERS",),
                    "layer": ("INT", {"default": 0, "min": 0}),
                }
                }

    RETURN_TYPES = ("MASK",)

    FUNCTION = "layers_to_mask"

    CATEGORY = category

    def layers_to_mask(self, segformer_layers, layer: int):

        alpha_mask = (segformer_layers == layer).astype(np.uint8)

        mask = torch.from_numpy(alpha_mask).type(torch.FloatTensor)

        return (mask, )
