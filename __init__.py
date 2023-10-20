from .MaskNodes import CustomMaskComposite
from .OurApiSend import OurApiSend
from .SegformerImageWithSemantic import SegformerImageWithSemantic, SegformerImageChooseLayer
from .TelegramSend import TelegramSend

NODE_CLASS_MAPPINGS = {
    "CustomMaskComposite": CustomMaskComposite,
    "OurApiSend": OurApiSend,
    "SegformerImageWithSemantic": SegformerImageWithSemantic,
    "SegformerImageChooseLayer": SegformerImageChooseLayer,
    "TelegramSend": TelegramSend
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CustomMaskComposite": "Custom mask composite"
}
