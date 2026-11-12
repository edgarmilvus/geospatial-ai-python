# Required structure for Exercise 2.
# A sketch, not a program: the two classes below are the interface to fill in.
import torch.nn as nn


class SEBlock(nn.Module):
    """
    Squeeze-and-Excitation Block for channel attention.
    """
    def __init__(self, channel, reduction=16):
        super(SEBlock, self).__init__()
        # 1. Global Average Pooling (Squeeze)
        # 2. Fully Connected Layers (Excitation)
        # 3. Sigmoid Activation
        pass

    def forward(self, x):
        # Implementation of the Squeeze, Excitation, and Scale operations.
        pass


class ModifiedUNet(nn.Module):
    # Assume standard U-Net structure defined here...

    def forward(self, x):
        # ... Encoder steps ...

        # Bottleneck Integration Point:
        # bottleneck_output = self.bottleneck_conv(bottleneck_input)
        # bottleneck_output = self.se_block(bottleneck_output) <-- Integration

        # ... Decoder steps ...
        pass
