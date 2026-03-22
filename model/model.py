import os
import cv2
import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
from scipy.io import loadmat
from torchvision import transforms
import torchvision.models as models
import torch.nn as nn
import random

torch.manual_seed(42)
np.random.seed(42)
random.seed(42)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

# PATH 
IMG_SIZE = 512
SIGMA = 4
BATCH_SIZE = 2
EPOCHS = 10
LR = 1e-5
DATA_ROOT = "shanghaitech_with_people_density_map/ShanghaiTech/part_A"

# ISKA MAP
def generate_density_map(points):
    density = np.zeros((IMG_SIZE, IMG_SIZE), dtype=np.float32)
    if len(points) == 0:
        return density
    for point in points:
        x = min(int(point[0]), IMG_SIZE - 1)
        y = min(int(point[1]), IMG_SIZE - 1)
        density[y, x] = 1
    density = cv2.GaussianBlur(density, (15, 15), SIGMA)
    return density

# KHANA
class ShanghaiDataset(Dataset):
    def __init__(self, root_path, augment=False):
        self.img_paths = []
        self.gt_paths = []
        self.augment = augment

        img_dir = os.path.join(root_path, 'images')
        gt_dir = os.path.join(root_path, 'ground-truth')

        for file in sorted(os.listdir(img_dir)):
            if file.endswith('.jpg'):
                self.img_paths.append(os.path.join(img_dir, file))
                gt_name = "GT_" + file.replace('.jpg', '.mat')
                self.gt_paths.append(os.path.join(gt_dir, gt_name))

        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

    def __len__(self):
        return len(self.img_paths)

    def __getitem__(self, idx):
        img = cv2.imread(self.img_paths[idx])
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        orig_h, orig_w = img.shape[:2]

        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))

        mat = loadmat(self.gt_paths[idx])
        points = mat["image_info"][0][0][0][0][0].copy()

        if len(points) > 0:
            points[:, 0] *= IMG_SIZE / orig_w
            points[:, 1] *= IMG_SIZE / orig_h

            if self.augment and random.random() > 0.5:
                img = cv2.flip(img, 1)
                points[:, 0] = (IMG_SIZE - 1) - points[:, 0]

        density = generate_density_map(points)

        density_small = cv2.resize(density,
                                   (IMG_SIZE // 8, IMG_SIZE // 8),
                                   interpolation=cv2.INTER_CUBIC)

        img = self.transform(img)
        density_small = torch.from_numpy(density_small).float().unsqueeze(0)
        return img, density_small, len(points)

# BHANG BHOSADA
class CSRNet(nn.Module):
    def __init__(self):
        super(CSRNet, self).__init__()
        vgg = models.vgg16(weights=models.VGG16_Weights.DEFAULT)
        features = list(vgg.features.children())

        self.frontend = nn.Sequential(*features[:23])
        self.backend = nn.Sequential(
            nn.Conv2d(512, 512, 3, padding=2, dilation=2), nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, 3, padding=2, dilation=2), nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, 3, padding=2, dilation=2), nn.ReLU(inplace=True),
            nn.Conv2d(512, 256, 3, padding=2, dilation=2), nn.ReLU(inplace=True),
            nn.Conv2d(256, 128, 3, padding=2, dilation=2), nn.ReLU(inplace=True),
            nn.Conv2d(128, 64,  3, padding=2, dilation=2), nn.ReLU(inplace=True),
        )
        self.output_layer = nn.Conv2d(64, 1, kernel_size=1)

        for param in self.frontend[:17].parameters():
            param.requires_grad = False
        for param in self.frontend[17:].parameters():
            param.requires_grad = True

    def forward(self, x):
        x = self.frontend(x)
        x = self.backend(x)
        x = self.output_layer(x)
        return x

#  DIGESION
if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

train_dataset = ShanghaiDataset(f"{DATA_ROOT}/train_data", augment=True)
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)

model = CSRNet().to(device)
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(
    filter(lambda p: p.requires_grad, model.parameters()), lr=LR
)
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

for epoch in range(EPOCHS):
    model.train()
    total_loss = 0

    for imgs, density, gt_counts in train_loader:
        imgs = imgs.to(device)
        density = density.to(device)

        preds = model(imgs)
        loss = criterion(preds, density)

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            filter(lambda p: p.requires_grad, model.parameters()), 1.0
        )
        optimizer.step()
        total_loss += loss.item()

    scheduler.step()
    print(f"Epoch {epoch+1}/{EPOCHS} — Loss: {total_loss/len(train_loader):.4f} "
          f"| LR: {scheduler.get_last_lr()[0]:.2e}")

# EVAL
test_dataset = ShanghaiDataset(f"{DATA_ROOT}/test_data", augment=False)
test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False)

model.eval()
mae, mse = 0, 0

print("\n── Per Image Results ──────────────────────────")
with torch.no_grad():
    for i, (imgs, density, gt_counts) in enumerate(test_loader):
        imgs = imgs.to(device)
        preds = model(imgs)

        pred_count = preds.sum().item()
        gt_count = gt_counts[0].item()
        error = abs(pred_count - gt_count)

        print(f"[{i+1:03d}] GT: {gt_count:6.1f} | Pred: {pred_count:6.1f} | Error: {error:5.1f}")
        print(f"       GT raw: {gt_count:.2f} | Pred raw sum: {pred_count:.2f}")

        mae += error
        mse += error ** 2

mae /= len(test_dataset)
mse = (mse / len(test_dataset)) ** 0.5

print(f"\n── Final Results ──────────────────────────────")
print(f"MAE : {mae:.2f}")
print(f"RMSE: {mse:.2f}")
torch.save(model.state_dict(), "csrnet.pth")
print("Model saved!")