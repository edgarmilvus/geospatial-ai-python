import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# One seed, one thread count: the loss curve below is a fixed number, not a sample.
SEED = 7
CHIP = 64            # a 64 x 64 chip keeps a full-batch epoch in milliseconds on CPU
N_CHIPS = 6
EPOCHS = 60
LEARNING_RATE = 0.05
REDUCTION = 16       # the SE bottleneck squeezes 64 channels to 4 and back


# --- 1. The Squeeze-and-Excitation Block ---
class SEBlock(nn.Module):
    """Channel attention: pool each channel, learn a weight per channel, rescale."""

    def __init__(self, channel, reduction=REDUCTION):
        super().__init__()
        # 1. Global Average Pooling (Squeeze): C x H x W -> C x 1 x 1
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        # 2. Two fully connected layers (Excitation), 64 -> 4 -> 64, no bias: the
        #    weight of a channel is a ratio, and a bias would let it drift.
        self.fc = nn.Sequential(
            nn.Linear(channel, channel // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channel // reduction, channel, bias=False),
            # 3. Sigmoid: a gate in (0, 1), not a signed additive term.
            nn.Sigmoid(),
        )

    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        # Scale: the block returns the same shape it received, reweighted.
        return x * y.expand_as(x)


# --- 2. The U-Net Components ---
class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.double_conv(x)


class Down(nn.Module):
    """One encoder step: halve the grid, double the channels."""

    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.block = nn.Sequential(nn.MaxPool2d(2), DoubleConv(in_channels, out_channels))

    def forward(self, x):
        return self.block(x)


class ModifiedUNet(nn.Module):
    """A small U-Net with the SE block between the bottleneck and the decoder."""

    def __init__(self, n_channels=3, n_classes=1, base=8):
        super().__init__()
        # Encoder: 64 -> 32 -> 16 pixels, 8 -> 16 -> 32 channels.
        self.inc = DoubleConv(n_channels, base)
        self.down1 = Down(base, base * 2)
        self.down2 = Down(base * 2, base * 4)
        # Bottleneck: the deepest block, at 16 x 16 with 64 channels.
        self.bottleneck_conv = DoubleConv(base * 4, base * 8)
        # Integration point: recalibrate the bottleneck before anything is upsampled.
        self.se_block = SEBlock(channel=base * 8, reduction=REDUCTION)
        # Decoder: the skip connections concatenate, so the first convolution of each
        # decoder block takes the upsampled channels plus the encoder's. up2 restores
        # 64 -> 32 channels at 32 pixels, and x2 brings 16 more.
        self.up2 = nn.ConvTranspose2d(base * 8, base * 4, kernel_size=2, stride=2)
        self.dec2 = DoubleConv(base * 4 + base * 2, base * 2)
        # up1 restores 16 -> 8 channels at 64 pixels, and x1 brings 8 more.
        self.up1 = nn.ConvTranspose2d(base * 2, base, kernel_size=2, stride=2)
        self.dec1 = DoubleConv(base + base, base)
        self.outc = nn.Conv2d(base, n_classes, kernel_size=1)

    def forward(self, x):
        x1 = self.inc(x)                     # (B, 8, 64, 64)
        x2 = self.down1(x1)                  # (B, 16, 32, 32)
        x3 = self.down2(x2)                  # (B, 32, 16, 16)
        bottleneck = self.bottleneck_conv(x3)   # (B, 64, 16, 16)
        bottleneck = self.se_block(bottleneck)  # same shape, channel weights applied
        y = self.dec2(torch.cat([self.up2(bottleneck), x2], dim=1))
        y = self.dec1(torch.cat([self.up1(y), x1], dim=1))
        return self.outc(y)                  # logits, (B, 1, 64, 64)


# --- 3. Synthetic Chips and Metrics ---
def synthetic_chip(rng, size=CHIP):
    """One RGB chip and its mask: one to three bright rectangular roofs."""
    image = rng.integers(70, 130, size=(3, size, size)).astype(np.float32)
    mask = np.zeros((1, size, size), dtype=np.float32)
    for _ in range(int(rng.integers(1, 4))):
        height = int(rng.integers(8, 22))
        width = int(rng.integers(8, 26))
        row = int(rng.integers(3, size - height - 3))
        col = int(rng.integers(3, size - width - 3))
        image[:, row:row + height, col:col + width] = rng.integers(205, 245)
        mask[:, row:row + height, col:col + width] = 1.0
    return image, mask


def build_batch(seed=SEED, n_chips=N_CHIPS):
    rng = np.random.default_rng(seed)
    chips = [synthetic_chip(rng) for _ in range(n_chips)]
    x = torch.from_numpy(np.stack([chip[0] for chip in chips])) / 255.0
    y = torch.from_numpy(np.stack([chip[1] for chip in chips]))
    return x, y


def iou(logits, targets, threshold=0.0):
    """Intersection over union at a logit threshold of 0 (a probability of 0.5)."""
    predicted = logits > threshold
    truth = targets > 0.5
    intersection = float((predicted & truth).sum())
    union = float((predicted | truth).sum())
    return intersection / union if union else 1.0


def train(model, x, y, epochs=EPOCHS, lr=LEARNING_RATE):
    """Full-batch training: six chips, no DataLoader, no worker, no shuffle."""
    torch.manual_seed(SEED)                  # the initial weights are fixed too
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCEWithLogitsLoss()
    history = []
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        loss = criterion(model(x), y)
        loss.backward()
        optimizer.step()
        history.append(float(loss.item()))
        if epoch == 0 or epoch == epochs - 1 or (epoch + 1) % 10 == 0:
            print(f"epoch {epoch + 1:2d}/{epochs}  loss {history[-1]:.5f}")
    return history


def parameter_table(model):
    """Count the parameters per block, so the SE block's share is visible."""
    return {name: sum(p.numel() for p in block.parameters())
            for name, block in model.named_children()}


# --- 4. Execution ---
def main():
    torch.manual_seed(SEED)                  # before the model is built, not after
    torch.set_num_threads(1)                 # one thread: the same curve on every machine

    model = ModifiedUNet()
    x, y = build_batch()
    print(f"Input batch: {tuple(x.shape)} {x.dtype}, range "
          f"[{float(x.min()):.2f}, {float(x.max()):.2f}]")
    print(f"Target batch: {tuple(y.shape)}, {int(y.sum())} roof pixels")

    with torch.no_grad():
        logits = model(x)
    print(f"Output logits: {tuple(logits.shape)}, range "
          f"[{float(logits.min()):.2f}, {float(logits.max()):.2f}]")

    # Requirement 3: the SE block must not change the bottleneck's shape.
    bottleneck = torch.zeros(2, 64, 16, 16)
    print(f"Bottleneck shape in/out of the SE block: "
          f"{tuple(bottleneck.shape)} -> {tuple(model.se_block(bottleneck).shape)}")

    table = parameter_table(model)
    total = sum(table.values())
    print("\n--- Parameters by block ---")
    for name, count in table.items():
        print(f"  {name:<16} {count:>8,}")
    print(f"  {'total':<16} {total:>8,}")
    print(f"The SE block is {table['se_block']} parameters: 64 x 4 plus 4 x 64, no bias.")

    print("\n--- Training ---")
    history = train(model, x, y)

    model.eval()
    with torch.no_grad():
        trained = model(x)
    print(f"\nLoss: first {history[0]:.5f}, last {history[-1]:.5f}")
    print(f"Training IoU at p = 0.5: {iou(trained, y):.4f}")

    # A held-out chip, drawn from a different seed: the test the training loss is not.
    x_val, y_val = build_batch(seed=SEED + 100, n_chips=2)
    with torch.no_grad():
        held_out = model(x_val)
    print(f"Held-out IoU at p = 0.5: {iou(held_out, y_val):.4f}")

    return {
        "logit_shape": tuple(int(v) for v in logits.shape),
        "logit_min": float(logits.min()),
        "logit_max": float(logits.max()),
        "parameters": table,
        "total_parameters": total,
        "se_parameters": table["se_block"],
        "loss_history": history,
        "loss_first": history[0],
        "loss_last": history[-1],
        "train_iou": iou(trained, y),
        "held_out_iou": iou(held_out, y_val),
        "roof_pixels": int(y.sum()),
        "batch_shape": tuple(int(v) for v in x.shape),
    }


if __name__ == "__main__":
    main()
