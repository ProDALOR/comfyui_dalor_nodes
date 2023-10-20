import torch


class CustomMaskComposite:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "destination": ("MASK",),
                "source": ("MASK",),
                "operation": (["multiply", "add", "subtract", "and", "or", "xor"],),
            }
        }

    CATEGORY = "mask"

    RETURN_TYPES = ("MASK",)

    FUNCTION = "combine"

    def combine(self, destination: torch.Tensor, source: torch.Tensor, operation: str):

        base_shape = destination.shape

        destination = destination.reshape(
            (-1, base_shape[-2], base_shape[-1])).clone()
        try:
            source = source.reshape((-1, base_shape[-2], base_shape[-1]))
        except:
            return (destination,)

        if operation == "multiply":
            result = destination * source
        elif operation == "add":
            result = destination + source
        elif operation == "subtract":
            result = destination - source
        elif operation == "and":
            result = torch.bitwise_and(
                destination.round().bool(), source.round().bool()).float()
        elif operation == "or":
            result = torch.bitwise_or(
                destination.round().bool(), source.round().bool()).float()
        elif operation == "xor":
            result = torch.bitwise_xor(
                destination.round().bool(), source.round().bool()).float()
        else:
            result = destination

        result = torch.clamp(result, 0.0, 1.0)

        return (result,)
