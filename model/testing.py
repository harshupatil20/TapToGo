import cv2
import time
import os
import torch
import torch.nn as nn
import torchvision.models as models
from torchvision import transforms

IMG_SIZE = 512
r = r"C:\Users\harah\OneDrive\Desktop\study\dataset\result.txt"

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

d = torch.device("cuda" if torch.cuda.is_available() else "cpu")
m = CSRNet()
m.load_state_dict(torch.load("csrnet.pth", map_location=d))
m.to(d)

def prd(f):
    m.eval()
    i = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
    i = cv2.resize(i, (IMG_SIZE, IMG_SIZE))
    t = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    x = t(i).unsqueeze(0).to(d)
    with torch.no_grad():
        return int(m(x).sum().item())

def sv(src, mn, mx):
    with open(r, 'w') as rc:
        rc.write(f"{src} - {mn} to {mx} people\n")
    print(f"Result saved: {src} - {mn} to {mx} people")

def run_image(path):
    if not os.path.exists(path):
        print("file not found")
        return
    f = cv2.imread(path)
    if f is None:
        print("could not read image")
        return
    c = prd(f)
    print(f"People count: {c}")
    sv(path, c, c)

def run_video(path):
    if not os.path.exists(path):
        print("file not found")
        return
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print("could not open video")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    tf = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    dur = tf / fps
    n = int(dur)
    interval = int(fps)

    print(f"Duration: {dur:.1f}s | sampling {n} frames (1 per sec)")

    counts = []
    for s in range(n):
        cap.set(cv2.CAP_PROP_POS_FRAMES, s * interval)
        e, f = cap.read()
        if not e:
            break
        c = prd(f)
        counts.append(c)
        print(f"  sec {s+1}: {c} people")

    cap.release()

    if counts:
        mn, mx = min(counts), max(counts)
        sv(path, mn, mx)
        print(f"\nResult: {mn} - {mx} people across {n} seconds")

def run_webcam():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("camera dead")
        return

    print("Webcam running — press Q to stop")
    counts = []
    t_start = time.time()
    batch = []
    batch_num = 0

    while True:
        e, f = cap.read()
        if not e:
            break

        elapsed = int(time.time() - t_start)
        cv2.putText(f, f"Time: {elapsed}s", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        if counts:
            cv2.putText(f, f"Last range: {counts[-1][0]}-{counts[-1][1]}",
                        (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Crowd Counter — press Q to quit", f)

        batch.append(f.copy())

        if len(batch) >= 10:
            batch_counts = [prd(fr) for fr in batch]
            mn, mx = min(batch_counts), max(batch_counts)
            counts.append((mn, mx))
            batch_num += 1
            sv("webcam", mn, mx)
            print(f"[batch {batch_num}] Range: {mn} - {mx} people")
            batch = []

        if cv2.waitKey(1000) & 0xFF == ord('q'):
            break

    if batch:
        batch_counts = [prd(fr) for fr in batch]
        mn, mx = min(batch_counts), max(batch_counts)
        sv("webcam", mn, mx)
        print(f"[final batch] Range: {mn} - {mx} people")

    cap.release()
    cv2.destroyAllWindows()
    print("Webcam stopped.")

# MENU
print("\n── Crowd Counter ──────────────────────────────")
print("1. Webcam")
print("2. Video file")
print("3. Image file")
ch = input("\nEnter choice (1/2/3): ").strip()

if ch == "1":
    run_webcam()
elif ch == "2":
    pp = input("Enter video path: ").strip().strip('"')
    run_video(pp)
elif ch == "3":
    pp = input("Enter image path: ").strip().strip('"')
    run_image(pp)
else:
    print("invalid choice")