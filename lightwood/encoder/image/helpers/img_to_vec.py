import torch
import torch.nn as nn
from lightwood.helpers.device import get_devices
from lightwood.helpers.torch import LightwoodAutocast

from lightwood.helpers.log import log

try:
    import torchvision.models as models
except ModuleNotFoundError:
    log.info("No torchvision detected, image helpers not supported.")


class ChannelPoolAdaptiveAvg1d(torch.nn.AdaptiveAvgPool1d):
    """
    Custom override of `torch.nn.AdaptiveAvgPool1d` to use `LightwoodAutocast()` and handle dimensions in the way we need to.
    """  # noqa
    def forward(self, input):
        with LightwoodAutocast():
            n, c, _, _ = input.size()
            input = input.view(n, c, 1).permute(0, 2, 1)
            pooled = torch.nn.functional.adaptive_avg_pool1d(input, self.output_size)
            _, _, c = pooled.size()
            pooled = pooled.permute(0, 2, 1)
            return pooled.view(n, c)


class Img2Vec(nn.Module):
    """ 
    Img2Vec is a ``torch.nn.module`` that returns image embeddings.
    
    For this, it uses a pretrained `torchvision.torch.resnext50_32x4d`, with its final fully connected layer removed.
    
    Output is a `self.output_size`-dimensioned vector, generated by taking the output of the Resnext's last convolutional layer and performing an adaptive channel pool average. 
    """  # noqa
    def __init__(self, device=''):
        super(Img2Vec, self).__init__()

        if(device == ''):
            self.device, _ = get_devices()
        else:
            self.device = torch.device(device)

        self.output_size = 512
        self.model = torch.nn.Sequential(*list(models.resnext50_32x4d(pretrained=True).children())[: -1],
                                         ChannelPoolAdaptiveAvg1d(output_size=self.output_size))
        self.model = self.model.to(self.device)

    def to(self, device, available_devices):
        self.device = device
        self.model = self.model.to(self.device)
        return self

    def forward(self, image, batch=True):
        with LightwoodAutocast():
            embedding = self.model(image.to(self.device))

            if batch:
                return embedding
            return embedding[0, :]
