from torchvision import transforms
from PIL import Image
import glob
import os
import torch

grey_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
    transforms.Grayscale(num_output_channels=1),
    transforms.ToTensor(),
])

color_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
    transforms.ToTensor(),
])

class ColorizationDataset(torch.utils.data.Dataset):
    def __init__(self, 
                 data_dir, 
                 grey_transform=grey_transform,
                 color_transform=color_transform):
        self.data_dir = data_dir
        self.grey_transform = grey_transform
        self.color_transform = color_transform
        self.image_paths = glob.glob(os.path.join(data_dir, "*.jpg"))

    def __getitem__(self, index):
        img = Image.open(self.image_paths[index]).convert("RGB")
        grey_img = self.grey_transform(img)
        color_img = self.color_transform(img)
        return grey_img, color_img

    def __len__(self):
        return len(self.image_paths)

