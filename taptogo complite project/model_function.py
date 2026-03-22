import cv2
import time
import os
import torch
import torch.nn as nn
import torchvision.models as models
from torchvision import transforms

IMG_SIZE = 512

class CSRNet(nn.Module):
    def __init__(self):
        super(CSRNet, self).__init__()
        vgg = models.vgg16(weights=models.VGG16_Weights.DEFAULT)
        features = list(vgg.features.children())
        self.frontend = nn.Sequential(*features[:23])
        self.backend = nn.Sequential(
            nn.Conv2d(512, 256, 3, padding=2, dilation=2), nn.ReLU(inplace=True),
            nn.Dropout2d(0.3),
            nn.Conv2d(256, 256, 3, padding=2, dilation=2), nn.ReLU(inplace=True),
            nn.Conv2d(256, 128, 3, padding=2, dilation=2), nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, 3, padding=2, dilation=2), nn.ReLU(inplace=True),
            nn.Conv2d(128, 64,  3, padding=2, dilation=2), nn.ReLU(inplace=True),
            nn.Conv2d(64,  64,  3, padding=2, dilation=2), nn.ReLU(inplace=True),
        )
        self.output_layer = nn.Conv2d(64, 1, kernel_size=1)

    def forward(self, x):
        x = self.frontend(x)
        x = self.backend(x)
        x = self.output_layer(x)
        return x


_d = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_m = CSRNet()
_m.load_state_dict(torch.load("csrnet.pth", map_location=_d))
_m.to(_d)
_m.eval()

def _prd(f):
    i = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
    i = cv2.resize(i, (IMG_SIZE, IMG_SIZE))
    t = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    x = t(i).unsqueeze(0).to(_d)
    with torch.no_grad():
        return int(_m(x).sum().item())

def image(path):

    if not os.path.exists(path):
        return None
    f = cv2.imread(path)
    if f is None:
        return None
    c = _prd(f)
    return c

def video(path):
   
    if not os.path.exists(path):
        return None, None
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return None, None

    fps = cap.get(cv2.CAP_PROP_FPS)
    tf = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    dur = tf / fps
    n = int(dur)
    interval = int(fps)

    counts = []
    for s in range(n):
        cap.set(cv2.CAP_PROP_POS_FRAMES, s * interval)
        e, f = cap.read()
        if not e:
            break
        counts.append(_prd(f))

    cap.release()

    if not counts:
        return None, None
    return min(counts), max(counts)

def webcam(on_result=None):
   
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return []

    all_results = []
    batch = []
    batch_num = 0
    t_start = time.time()

    while True:
        e, f = cap.read()
        if not e:
            break

        elapsed = int(time.time() - t_start)
        cv2.putText(f, f"Time: {elapsed}s", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        if all_results:
            cv2.putText(f, f"Last range: {all_results[-1][0]}-{all_results[-1][1]}",
                        (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Crowd Counter — press Q to quit", f)

        batch.append(f.copy())

        if len(batch) >= 10:
            batch_counts = [_prd(fr) for fr in batch]
            mn, mx = min(batch_counts), max(batch_counts)
            all_results.append((mn, mx))
            batch_num += 1
            if on_result:
                on_result(mn, mx)
            batch = []

        if cv2.waitKey(1000) & 0xFF == ord('q'):
            break

    if batch:
        batch_counts = [_prd(fr) for fr in batch]
        mn, mx = min(batch_counts), max(batch_counts)
        all_results.append((mn, mx))
        if on_result:
            on_result(mn, mx)

    cap.release()
    cv2.destroyAllWindows()
    return all_results