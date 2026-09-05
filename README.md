<div align="center">

# VOX: hand signals from a smartwatch

Yuhyeon Lee · 2025

[![checks](https://img.shields.io/github/actions/workflow/status/blueion0612/VOX/checks.yml?branch=main&label=checks)](https://github.com/blueion0612/VOX/actions/workflows/checks.yml)
[![License](https://img.shields.io/github/license/blueion0612/VOX)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-coursework-orange)](#limitations)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)](#requirements)

[**Report**](capstone_report.pdf) · [**Slides**](capstone_slides.pptx) · [**Streaming app**](https://github.com/wearable-motion-capture/sensor-stream-apps) · [**Related**](#related)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/figures/hero_models-dark.png">
  <img alt="Accuracy of five architectures, on the public 6DMG dataset under cross-validation and on the project's own recordings under three filter settings" src="docs/figures/hero_models.png">
</picture>

</div>

*Parsed from the training logs under `Model/`, so the figure cannot drift from what
was run. Regenerate with `python docs/figures/make_hero.py`.*

**VOX** reads a hand signal from a smartwatch and sends it to a command post. It was
built for firefighting and policing, where the radios in use are half duplex, so only
one person can speak at a time, and where operating one at all is hard in the middle
of an emergency. A gesture needs no free hand on a radio and no channel.

The arm pose is estimated continuously from the watch and drawn in Unity; a gesture
is recorded on a key press, classified, and the result goes out over UDP to a server.

Undergraduate capstone project, Myongji University, 2025. Team of three; the machine
learning, the Python pipeline and this repository are the author's part.

## Results

Three signals are recognized: **V**, **X** and **circle**. Five architectures were
trained on two sources, and the deployed model is CNN-BiLSTM on high-pass filtered
recordings.

**Public dataset, 6DMG, five-fold cross-validation:**

| Model | Accuracy (%) |
|---|---:|
| BiLSTM | 96.79 ± 1.23 |
| GRU | 93.22 ± 3.55 |
| CNN | 96.67 ± 1.70 |
| CNN-BiLSTM | 97.62 ± 1.88 |
| **TCN** | **99.05 ± 0.80** |

**Own recordings, 60 held-out samples, 20 per class:**

| Model | No filter | High-pass | Low + high-pass |
|---|---:|---:|---:|
| BiLSTM | 98.33 | 96.67 | 98.33 |
| GRU | 93.33 | 90.00 | 90.00 |
| CNN | 98.33 | 98.33 | 98.33 |
| **CNN-BiLSTM** | 95.00 | **100.00** | **100.00** |
| TCN | 100.00 | 95.00 | 95.00 |

**Sixty test samples means one sample is 1.67 points.** The gap between 95 and 100 in
that second table is three samples, so the ordering inside it is not firm. The
cross-validated numbers on the public dataset are the ones worth comparing, and there
the ranking is different: TCN leads offline while CNN-BiLSTM leads on the recordings.

## Quick start

The watch and phone must be paired over Bluetooth, and the phone and the machine
running VOX must be on the same network, since the sensor stream is broadcast.

1. Clone this repository and `pip install -e .`, which brings in PyTorch, NumPy,
   SciPy and pandas.
2. Install the [sensor stream apps](https://github.com/wearable-motion-capture/sensor-stream-apps)
   on the watch and phone.
3. Find the machine's address with `ipconfig`, enter it in the phone app, and put the
   phone in a pocket.
4. On the watch, start the app, choose **Pocket**, hold the arm up at ninety degrees
   as if reading the watch until alignment completes, then press **stream IMU**.
5. Start the Unity visualizer.
6. Run the classifier:

```bash
python watch_phone_pocket_classification.py <your IP> \
    Model/Online_with_HPF/online_gesture_cnnbilstm.pth cnnbilstm
```

Hold **right shift** while making a signal. Recording starts on the press and
classification runs on release; the result is sent to the configured server. Press
enter to quit.

## Usage

The live classifier is the command Quick start ends with. The evaluation tool and
the figure script are the other two entry points.

`evaluate_models.py` reports more than accuracy, because a model that has to run on a
stream is not chosen on accuracy alone: parameter count, FLOPs per prediction, file
size, inference time per sample, and the confidence the model assigned when it was
right, including its lowest such confidence.

```bash
python vox/classification/evaluate_models.py \
    --csv Data/Test/vxo_gesture.csv \
    --models Model/Online_with_HPF/online_gesture_{bilstm,gru,simplecnn,cnnbilstm,smalltcn}.pth \
    --model-types bilstm gru simplecnn cnnbilstm smalltcn
```

Per-model confusion matrices, loss and F1 curves are under `Model/`, one folder per
architecture and filter setting. `python docs/figures/make_hero.py` redraws the hero
from the training logs, and CI fails if a number in the README stops matching them.

## Method

### Pose first, gesture second

The watch and pocketed phone give inertial data only;
arm pose is estimated from it continuously and rendered in Unity, and the gesture
classifier reads the same stream.

### A high-pass filter is what the deployment uses

Without it a model can lean on
the arm's resting orientation, which is constant within a recording session and
carries no information about the movement. Filtering it out costs accuracy on some
architectures and gains it on others, as the table above shows.

### Two data sources

The public 6DMG dataset, converted from MATLAB to CSV, gives
enough data for five-fold cross-validation. Recordings made with the watch itself
give a smaller set that matches the deployment conditions, and the models were
trained on both separately rather than pooled.

## Repository layout

```
vox/                     the Python package
  classification/        training, offline and online, plus model evaluation
  data_types/            bone and pose structures
  data_deploy/           exported model bundles
Data/
  Offline/               6DMG, converted to CSV
  Online/                recordings made with the watch
  Test/                  the held-out set used for evaluation
Model/
  Offline/               trained on 6DMG, with curves and confusion matrices
  Online_without_filter/ | Online_with_HPF/ | Online_with_LPF_HPF/
visualization/           Unity arm pose visualizer
webserver/               the receiving end of the UDP messages
docs/figures/            README figure, the script that draws it, figstyle.py
watch_phone_pocket_classification.py    live classification entry point
pyproject.toml           the vox package and its dependencies
```

## Requirements

Python 3.9 or newer with PyTorch, NumPy, SciPy and pandas. Unity for the visualizer.
A WearOS watch and an Android phone running the sensor stream apps.

## Limitations

- **Three signals.** V, X and circle, which is enough to show the idea and not enough
  to be a vocabulary.
- **Sixty test samples**, one wearer. The ordering between the closer models is
  within noise.
- **Gestures are recorded on a key press**, not spotted in a continuous stream, so
  nothing here solves the harder problem of deciding when a signal has begun.
- **Same network required.** The sensor stream is broadcast over UDP with no
  discovery and no acknowledgement.
- Built and run on Windows, with paths and a key binding to match.

## Related

- [IMU_Stream_APP_MJU](https://github.com/blueion0612/IMU_Stream_APP_MJU): the
  author's fork of the same streaming apps, sending a reduced 30-float packet. VOX
  uses the upstream apps unchanged.
- [IVO](https://github.com/blueion0612/IVO): the sibling capstone, smartwatch
  gestures driving a presentation instead of a radio.
- [IMU_Gesture_Classifier](https://github.com/blueion0612/IMU_Gesture_Classifier):
  fifteen gestures from the same kind of signal, with a two-stage detector.

## Credits

Team of three. This repository holds the machine learning, the Python pipeline and
the evaluation. The arm pose visualizer is built on
[arm-pose-visualization](https://github.com/wearable-motion-capture/arm-pose-visualization)
and the streaming apps on
[sensor-stream-apps](https://github.com/wearable-motion-capture/sensor-stream-apps),
both from the wearable-motion-capture project.

## License

MIT. See [LICENSE](LICENSE).
