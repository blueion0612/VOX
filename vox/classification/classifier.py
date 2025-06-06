import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

class BiLSTMClassifier(nn.Module):
    """
    RNN-BiLSTM many-to-one classifier with packing for padded sequences:
    - Input: (batch, C=6, T) + lengths
    - Bidirectional LSTM layer with 110 hidden units
    - Fully connected output layer (num_classes)
    """
    def __init__(self, input_size=6, hidden_size=110, num_layers=1, num_classes=3):
        super(BiLSTMClassifier, self).__init__()
        self.lstm = nn.LSTM(
            input_size,
            hidden_size,
            num_layers,
            batch_first=True,
            bidirectional=True,
        )
        self.fc = nn.Linear(hidden_size * 2, num_classes)

    def forward(self, x, lengths):
        # x: [batch, C, T] -> [batch, T, C]
        x = x.transpose(1, 2)
        # Pack padded sequence, ignore padded steps
        packed, _ = pack_padded_sequence(x, lengths, batch_first=True, enforce_sorted=False), None
        packed_out, (h_n, c_n) = self.lstm(packed)
        # Use last layer's forward and backward hidden states
        forward_hidden = h_n[-2]
        backward_hidden = h_n[-1]
        h = torch.cat((forward_hidden, backward_hidden), dim=1)
        logits = self.fc(h)
        return logits

class GRUClassifier(nn.Module):
    """
    RNN-GRU many-to-one classifier with packing for padded sequences:
    - 3-layer GRU: 256 -> 128 -> 64 units
    - Fully connected output layer (num_classes)
    """
    def __init__(self, input_size=6, hidden_sizes=(256,128,64), num_classes=3):
        super(GRUClassifier, self).__init__()
        self.gru1 = nn.GRU(input_size, hidden_sizes[0], batch_first=True)
        self.gru2 = nn.GRU(hidden_sizes[0], hidden_sizes[1], batch_first=True)
        self.gru3 = nn.GRU(hidden_sizes[1], hidden_sizes[2], batch_first=True)
        self.fc   = nn.Linear(hidden_sizes[2], num_classes)

    def forward(self, x, lengths):
        # x: [batch, C, T] -> [batch, T, C]
        x = x.transpose(1, 2)
        # Pack padded sequence, ignore padded steps
        packed, _ = pack_padded_sequence(x, lengths, batch_first=True, enforce_sorted=False), None
        # Pass through GRU layers, ignore intermediate hidden outputs
        packed, _ = self.gru1(packed)
        packed, _ = self.gru2(packed)
        packed, h_last = self.gru3(packed)
        # h_last: (1, batch, hidden_size), squeeze batch dimension
        h_last = h_last.squeeze(0)
        logits = self.fc(h_last)
        return logits

class SimpleCNNClassifier(nn.Module):
    """
    Lightweight 1D-CNN for IMU gesture classification (offline).
    Input: (batch, C=6, T=150)
    - Conv1: 6→64, kernel=3, padding=1 → ReLU → MaxPool1d(2)   # T:150→75
    - Conv2: 64→64, kernel=3, padding=1 → ReLU → MaxPool1d(2)  # T:75→37
    - Flatten → FC1(64*37→64) → ReLU → Dropout(0.3) → FC2(64→num_classes)
    """
    def __init__(self, num_channels=6, num_classes=3):
        super(SimpleCNNClassifier, self).__init__()
        self.conv1 = nn.Conv1d(num_channels, 64, kernel_size=3, padding=1, bias=True)
        self.relu1 = nn.ReLU(inplace=True)
        self.pool1 = nn.MaxPool1d(kernel_size=2, stride=2)  # 150→75

        self.conv2 = nn.Conv1d(64, 64, kernel_size=3, padding=1, bias=True)
        self.relu2 = nn.ReLU(inplace=True)
        self.pool2 = nn.MaxPool1d(kernel_size=2, stride=2)  # 75→37

        self.fc1 = nn.Linear(64 * 37, 64, bias=True)
        self.relu_fc = nn.ReLU(inplace=True)
        self.dropout = nn.Dropout(p=0.3)
        self.fc2 = nn.Linear(64, num_classes, bias=True)

    def forward(self, x, lengths=None):
        # x: (batch, 6, 150)
        x = self.conv1(x)     # → (batch,64,150)
        x = self.relu1(x)
        x = self.pool1(x)     # → (batch,64,75)
        x = self.conv2(x)     # → (batch,64,75)
        x = self.relu2(x)
        x = self.pool2(x)     # → (batch,64,37)

        x = x.view(x.size(0), -1)        # → (batch,64*37)
        x = self.relu_fc(self.fc1(x))    # → (batch,64)
        x = self.dropout(x)
        logits = self.fc2(x)             # → (batch,num_classes)
        return logits


import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence

class CNNBiLSTMClassifier(nn.Module):
    """
    Offline hybrid model: CNN → BiLSTM → FC
    - Input: (batch, C=6, T=150)
    - Conv1: 6→32, kernel=3, padding=1 → ReLU → MaxPool1d(2)   # 150→75
    - Conv2: 32→64, kernel=3, padding=1 → ReLU → MaxPool1d(2)  # 75→37
    - → transpose → (batch,37,64)
    - BiLSTM(input=64, hidden=64, num_layers=1, bidirectional=True)
    - h_cat = concat(last fwd & bwd hidden) → (batch,128)
    - FC(128→num_classes)
    """
    def __init__(self, num_channels=6, num_classes=3):
        super(CNNBiLSTMClassifier, self).__init__()
        # CNN 부분
        self.conv1 = nn.Conv1d(num_channels, 32, kernel_size=3, padding=1, bias=True)
        self.relu1 = nn.ReLU(inplace=True)
        self.pool1 = nn.MaxPool1d(kernel_size=2, stride=2)  # 150→75

        self.conv2 = nn.Conv1d(32, 64, kernel_size=3, padding=1, bias=True)
        self.relu2 = nn.ReLU(inplace=True)
        self.pool2 = nn.MaxPool1d(kernel_size=2, stride=2)  # 75→37

        # BiLSTM 부분
        self.lstm = nn.LSTM(
            input_size=64,
            hidden_size=64,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )

        # FC 레이어
        self.fc = nn.Linear(64 * 2, num_classes)

    def forward(self, x, lengths=None):
        # lengths는 offline에서는 모두 동일 길이(150)이므로 사용하지 않음
        # x: (batch, 6, 150)
        x = self.conv1(x)   # → (batch,32,150)
        x = self.relu1(x)
        x = self.pool1(x)   # → (batch,32,75)
        x = self.conv2(x)   # → (batch,64,75)
        x = self.relu2(x)
        x = self.pool2(x)   # → (batch,64,37)

        x = x.transpose(1, 2)  # → (batch,37,64)
        # BiLSTM: pack_padded_sequence 불필요 (고정 길이 37)
        out, (h_n, _) = self.lstm(x)  
        # h_n: (2, batch, 64)  → 마지막 레이어의 fwd/bwd
        h_fwd = h_n[-2]  # (batch,64)
        h_bwd = h_n[-1]  # (batch,64)
        h_cat = torch.cat([h_fwd, h_bwd], dim=1)  # (batch,128)

        logits = self.fc(h_cat)  # (batch,num_classes)
        return logits
    

import torch
import torch.nn as nn

class TemporalBlock(nn.Module):
    """
    TCN 기본 블록: in_channels→out_channels
    - kernel_size=3, dilation=2^i
    - padding=(kernel_size−1)*dilation → 시퀀스 길이 유지
    - residual connection: in→out 매핑(1×1 Conv) 필요 시
    """
    def __init__(self, in_channels, out_channels, kernel_size=3, dilation=1, dropout=0.2):
        super(TemporalBlock, self).__init__()
        padding = ((kernel_size - 1) * dilation) // 2

        self.conv1 = nn.Conv1d(
            in_channels, out_channels, kernel_size,
            stride=1, padding=padding, dilation=dilation, bias=False
        )
        self.bn1   = nn.BatchNorm1d(out_channels)
        self.relu1 = nn.ReLU(inplace=True)
        self.drop1 = nn.Dropout(dropout)

        self.conv2 = nn.Conv1d(
            out_channels, out_channels, kernel_size,
            stride=1, padding=padding, dilation=dilation, bias=False
        )
        self.bn2   = nn.BatchNorm1d(out_channels)
        self.relu2 = nn.ReLU(inplace=True)
        self.drop2 = nn.Dropout(dropout)

        if in_channels != out_channels:
            self.downsample = nn.Conv1d(in_channels, out_channels, kernel_size=1, bias=False)
            self.bn_ds = nn.BatchNorm1d(out_channels)
        else:
            self.downsample = None

        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu1(out)
        out = self.drop1(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu2(out)
        out = self.drop2(out)

        res = x if self.downsample is None else self.bn_ds(self.downsample(x))
        return self.relu(out + res)


class SmallTCNClassifier(nn.Module):
    """
    Offline TCN 모델
    - Input: (batch, C=6, T=150)
    - 3개 TemporalBlock 쌓기 (채널=[32,64,64], dilation=[1,2,4])
    - 출력 y: (batch,64,150)
    - Flatten 없이 Global Pooling(평균) → (batch,64)
    - FC(64→num_classes)
    """
    def __init__(self, in_channels=6, num_classes=3,
                 num_channels=[32, 64, 64], kernel_size=3, dropout=0.2):
        super(SmallTCNClassifier, self).__init__()
        layers = []
        for i, out_ch in enumerate(num_channels):
            in_ch = in_channels if i == 0 else num_channels[i - 1]
            dilation_size = 2 ** i
            layers.append(
                TemporalBlock(
                    in_channels=in_ch,
                    out_channels=out_ch,
                    kernel_size=kernel_size,
                    dilation=dilation_size,
                    dropout=dropout
                )
            )
        self.network = nn.Sequential(*layers)  # → (batch,64,150)
        self.fc = nn.Linear(num_channels[-1], num_classes)

    def forward(self, x, lengths=None):
        # lengths 없음 (offline)
        y = self.network(x)  # → (batch,64,150)
        # Global average pooling: 시간축(150)에 대해 평균
        y_pool = y.mean(dim=2)  # → (batch,64)
        logits = self.fc(y_pool)  # → (batch, num_classes)
        return logits
