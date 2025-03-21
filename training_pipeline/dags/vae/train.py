import os
import numpy as np
import torch
import yaml
from torch import optim
import torch.nn.functional as F
from torch.utils.data import DataLoader
from model import VAE_CNN_Improved
from loader import ColorizationDataset

def seed_everything(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def loss_function(x, x_recon, mu, logvar):
    x_recon = x_recon.detach().cpu()
    MSE = F.mse_loss(x_recon, x, reduction='sum')
    KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    return MSE + KLD


def get_data_loaders(config):
    data_dir = config["data_dir"]
    batch_size = config["batch_size"]
    train_path = os.path.join(data_dir, "train")
    val_path = os.path.join(data_dir, "val")
    train_set = ColorizationDataset(train_path)
    val_set = ColorizationDataset(val_path)
    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, pin_memory=True)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False, pin_memory=True)
    return train_loader, val_loader

def save_model(model, path):
    torch.save(model.state_dict(), path)

def train_model(train_loader, val_loader, config):
    device = torch.device(config["device"])
    model = VAE_CNN_Improved(latent_dim=config["latent_dim"]).to(device)
    optimizer = optim.AdamW(model.parameters(), lr=1e-3)
    loss_history, latent_history = [], []
    for epoch in range(config["num_epochs"]):
        model.train()
        train_loss = 0
        for grey_img, img in train_loader:
            grey_img = grey_img.to(device)
            optimizer.zero_grad()
            x_recon, mu, logvar, z = model(grey_img)
            loss = loss_function(img, x_recon, mu, logvar)
            loss.backward()
            train_loss += loss.item()
            optimizer.step()
        avg_loss = train_loss / len(train_loader.dataset)
        loss_history.append(avg_loss)
        print(f"Epoch {epoch+1}/{config["num_epochs"]}, Loss: {avg_loss:.4f}")

        model.eval()
        with torch.no_grad():
            latent = []
            for grey_img, img in val_loader:
                grey_img = grey_img.to(device)
                x_recon, mu, logvar, z = model(grey_img)
                latent.append(z)
            latent_history.append(torch.cat(latent))
    save_model(model, "./model.pth")
    return loss_history, latent_history



if __name__ == "__main__":
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    seed_everything(config["seed"])
    train_loader, val_loader = get_data_loaders(config)
    loss_history, latent_history = train_model(train_loader, val_loader, config)
