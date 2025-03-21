import torch
from torch import nn

class VAE_CNN_Improved(nn.Module):
    def __init__(self, latent_dim=128):
        super(VAE_CNN_Improved, self).__init__()
        self.latent_dim = latent_dim

        # Encoder với BatchNorm để ổn định batch size lớn
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, stride=2, padding=1),  # 32x32 -> 16x16
            nn.BatchNorm2d(32),
            nn.SiLU(),
            nn.Dropout2d(0.05),

            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),  # 16x16 -> 8x8
            nn.BatchNorm2d(64),
            nn.SiLU(),
            nn.Dropout2d(0.1),

            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),  # 8x8 -> 4x4
            nn.BatchNorm2d(128),
            nn.SiLU(),
            nn.Dropout2d(0.15),

            nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1),  # 4x4 -> 2x2
            nn.BatchNorm2d(256),
            nn.SiLU(),
            nn.Dropout2d(0.2),

            nn.Conv2d(256, 512, kernel_size=3, stride=2, padding=1),  # 2x2 -> 1x1
            nn.BatchNorm2d(512),
            nn.SiLU(),
            nn.Flatten()
        )

        # FC layers cho latent space
        self.fc_mu = nn.Linear(512*7*7, latent_dim)
        self.fc_logvar = nn.Linear(512*7*7, latent_dim)

        # Decoder: dùng ConvTranspose với BatchNorm để tăng độ mượt của ảnh
        self.decoder_input = nn.Linear(latent_dim, 512)

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(512, 256, kernel_size=3, stride=2, padding=1, output_padding=1),  # 1x1 -> 2x2
            nn.BatchNorm2d(256),
            nn.SiLU(),
            nn.Dropout2d(0.2),

            nn.ConvTranspose2d(256, 128, kernel_size=3, stride=2, padding=1, output_padding=1),  # 2x2 -> 4x4
            nn.BatchNorm2d(128),
            nn.SiLU(),
            nn.Dropout2d(0.15),

            nn.ConvTranspose2d(128, 64, kernel_size=3, stride=2, padding=1, output_padding=1),  # 4x4 -> 8x8
            nn.BatchNorm2d(64),
            nn.SiLU(),
            nn.Dropout2d(0.1),

            nn.ConvTranspose2d(64, 32, kernel_size=3, stride=2, padding=1, output_padding=1),  # 8x8 -> 16x16
            nn.BatchNorm2d(32),
            nn.SiLU(),
            nn.Dropout2d(0.05),

            nn.ConvTranspose2d(32, 3, kernel_size=3, stride=2, padding=1, output_padding=1),  # 16x16 -> 32x32
            nn.Tanh()
        )

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def forward(self, x):
        h = x

        shortcuts = []
        for block in self.encoder:
            h = block(h)
            if isinstance(block, nn.SiLU):
                shortcuts.append(h)
        
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        z = self.reparameterize(mu, logvar)

        h_dec = self.decoder_input(z).view(-1, 512, 1, 1)

        for block in self.decoder:
            if isinstance(block, nn.ConvTranspose2d):
                shortcut = shortcuts.pop()
                h_dec = h_dec + shortcut
            h_dec = block(h_dec)
        
        x_recon = h_dec
        return x_recon, mu, logvar, z
    
