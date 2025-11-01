# 3D Medical Visualization System 🏥

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)

A comprehensive 3D medical imaging and visualization platform for anatomical education and learning. This system provides advanced rendering techniques and interactive navigation tools for multiple organ systems.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Demo](#-demo)
- [Features](#-features)
- [System Architecture](#%EF%B8%8F-system-architecture)
- [Supported Medical Systems](#-supported-medical-systems)
- [Installation](#-installation)
- [Usage Guide](#-usage-guide)
- [Visualization Techniques](#-visualization-techniques)
- [Navigation Methods](#-navigation-methods)
- [Advanced Features](#-advanced-features)
- [Technical Stack](#-technical-stack)
- [File Structure](#-file-structure)
- [Requirements](#-requirements)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 🎯 Overview

This 3D Medical Visualization System is a powerful educational tool designed to provide realistic, interactive visualization of human anatomy. Built with VTK and PyQt5, it supports multiple organ systems with advanced rendering capabilities, real-time data integration, and intuitive navigation controls.

### Key Highlights
- **Multi-System Support**: Cardiovascular, Nervous, Musculoskeletal, and Dental systems
- **Real-Time Data Integration**: ECG/EEG signal visualization synchronized with 3D models
- **Advanced Rendering**: Surface rendering, clipping planes, curved MPR, and orthogonal slicing
- **Interactive Navigation**: Focus mode, fly-through, and real-time manipulation
- **Anatomically Accurate**: Realistic colors and proportions based on medical literature

---

## 🎬 Demo

**Cardiovascular System**
*Surface rendering of heart anatomy with realistic coloring and ECG-synchronized heart contraction with blood flow*



**Nervous System**
*3D brain model with cortical surface detail, Real-time EEG electrical signal propagation and Curved MPR for neural tract visualization*



**Dental**
*High-detail dental and jaw anatomy and Curved MPR along dental arch*



**Musculoskeletal System**
*Complete leg musculoskeletal visualization and Cross-sectional view with clipping planes*


---

## ✨ Features

### 🎨 Visualization Modes
- **Surface Rendering**: High-quality 3D surface visualization with realistic lighting
- **Clipping Planes**: Cross-sectional views with adjustable X/Y axis slicing
- **Curved MPR**: Multi-planar reconstruction along curved paths
- **Volume Rendering**: Direct volume visualization from DICOM data

### 🧭 Navigation Tools
- **Focus Navigation**: Zoom and highlight specific anatomical components
- **Fly-Through Mode**: Cinematic camera paths through 3D models
- **Interactive Rotation**: Mouse-controlled model manipulation
- **Auto-Flythrough**: Automated camera movement with customizable endpoints

### 📊 Data Integration
- **ECG Visualization**: Real-time cardiac electrical activity mapped to heart chambers
- **EEG Mapping**: Brain electrical signals displayed on cortical surface
- **DICOM Support**: Load medical imaging data from CT/MRI scans
- **NIfTI Support**: Neuroimaging data format compatibility
- **Batch Import**: Load multiple OBJ files simultaneously

### 🎛️ User Controls
- **Opacity Adjustment**: Fine-tune transparency for layered viewing
- **Component Toggle**: Show/hide individual anatomical parts
- **Speed Control**: Adjust animation playback speed
- **Color Coding**: Anatomically accurate tissue coloring

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Main GUI (gui.py)                    │
│              Medical Systems Selection Hub               │
└───────────┬─────────────────────────────────┬───────────┘
            │                                 │
    ┌───────▼────────┐                ┌──────▼─────────┐
    │  System GUIs   │                │  Visualization │
    │  - heart_gui   │                │    Modules     │
    │  - brain_gui   │                │  - flyThrough  │
    │  - legs_gui    │                │  - clipping    │
    │  - teeth_gui   │                │  - curvedMPR   │
    └───────┬────────┘                └──────┬─────────┘
            │                                 │
    ┌───────▼─────────────────────────────────▼───────┐
    │              VTK Rendering Engine               │
    │         (3D Graphics & Interaction)             │
    └─────────────────────────────────────────────────┘
```

---

## 🫀 Supported Medical Systems

### 1. Cardiovascular System (❤️)
- **Components**: Ventricles, atria, valves, coronary arteries, veins
- **Special Features**:
  - ECG-synchronized heart pumping animation
  - Realistic blood flow visualization
  - Chamber-specific contraction sequences
  - Separate phase timing for each chamber

### 2. Nervous System (🧠)
- **Components**: Cerebral cortex, white matter, cerebellum, brainstem, blood vessels
- **Special Features**:
  - EEG electrode mapping (10-20 system)
  - Real-time electrical signal propagation
  - Surface-based signal paths
  - Curved MPR for tract visualization

### 3. Musculoskeletal System (🦵)
- **Components**: Bones, muscles, tendons, ligaments, cartilage
- **Special Features**:
  - Smart color detection (bone vs. muscle vs. tendon)
  - Regional anatomy display
  - Clipping planes for internal structure viewing

### 4. Dental System (🦷)
- **Components**: Teeth, gums, alveolar bone, pulp, jaw
- **Special Features**:
  - High-specular tooth surface rendering
  - Curved MPR for dental arch analysis
  - Detailed intraoral anatomy

---

## 🚀 Installation

### Prerequisites
```bash
Python 3.8+
pip (Python package manager)
```

### Required Libraries
```bash
pip install PyQt5 vtk numpy scipy matplotlib pillow opencv-python
pip install mne nibabel pydicom vispy
```

### Optional Libraries (for advanced features)
```bash
pip install scikit-image SimpleITK
```

### Installation Steps
1. Clone the repository:
```bash
git clone https://github.com/RadwaHa/3D-Medical-Visualization.git
cd 3D-Medical-Visualization
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the main application:
```bash
python src/gui.py
```

---

## 📖 Usage Guide

### Starting the Application
1. Launch the main GUI:
   ```bash
   python src/gui.py
   ```

2. Select your desired medical system (Cardio, Skeleton, Nervous, or Dental)

3. Choose a visualization mode or navigation technique

### Loading 3D Models
- **Single File**: Click "Load Single OBJ File" and select a .obj file
- **Batch Import**: Click "Load Folder (Batch Import)" to load multiple files at once

### Loading Medical Imaging Data
- **DICOM**: For CT/MRI data, use the clipping planes or orthogonal viewer
- **NIfTI**: Brain imaging data loads automatically in curved MPR mode
- **EDF/EEG**: Electrical signal data integrates with brain models

### Basic Controls
- **Rotate**: Left-click and drag
- **Zoom**: Scroll wheel or +/- keys
- **Pan**: Middle-click and drag
- **Reset**: Click "Reset" button to restore default view

---

## 🎨 Visualization Techniques

### Surface Rendering
Displays the outer surface of anatomical structures with realistic lighting and shading.

**Usage**:
1. Load your 3D models
2. Click "Surface Rendering" button
3. Adjust opacity slider for transparency

**Best For**: General anatomy overview, external structure examination

---

### Clipping Planes
Creates cross-sectional views by slicing through the model along X or Y axes.

**Usage**:
1. Click "Clipping Planes" button
2. Enable X-axis or Y-axis clipping
3. Adjust slider to move the cutting plane
4. Use "Invert" to reverse the cutting direction

**Best For**: Internal structure examination, layer-by-layer analysis

---

### Curved MPR (Multi-Planar Reconstruction)
Generates curved cross-sections following user-defined paths.

**Supported Systems**: Nervous, Dental

**Usage**:
1. Draw a curved path on the 2D slice view
2. Select viewing side (concave/convex)
3. Adjust thickness slider
4. Click "Generate Curved MPR"

**Best For**: Dental arch analysis, nerve tract following, curved anatomical pathways

---

## 🧭 Navigation Methods

### Focus Navigation
Isolates and zooms into specific anatomical components.

**Usage**:
1. Click "Focus Navigation"
2. Select component from dropdown
3. Click "Focus" - camera smoothly animates to target
4. Click "Reset Focus" to restore full view

**Features**:
- Smooth camera animation (800ms transition)
- Other parts fade to 25% opacity
- Maintains spatial context

---

### Fly-Through Mode
Provides cinematic navigation through 3D models with automatic or manual control.

**Usage**:
1. Click "Fly-through Mode"
2. Navigate manually using keyboard:
   - `Space`: Move forward
   - `Ctrl`: Move backward
   - `Arrow Keys`: Rotate view
   - `+/-`: Zoom in/out
3. Set endpoint for automatic flythrough:
   - Position camera at desired start
   - Click "Set End Point (Current View)"
   - Click "Start Auto Flythrough"

**Features**:
- Real-time 3D rendering
- Customizable speed (10-200%)
- Smooth interpolation between waypoints
- Interactive and automatic modes

---

## 🔬 Advanced Features

### ECG Heart Pumping Visualization
Real-time cardiac animation synchronized with ECG data.

**Components**:
- Automatic ECG extraction from PNG images
- Synthetic ECG generation as fallback
- Per-chamber contraction timing
- Realistic blood flow particles

**Technical Details**:
- Detects P-waves, QRS complexes, T-waves
- Right atrium contracts 30ms before left atrium
- Right ventricle contracts 10ms before left ventricle
- Smooth deformation using wall-thickening algorithm

**Usage**:
1. From Heart System, click "ECG Heart Pumping"
2. Provide ECG folder path or use synthetic data
3. Adjust playback speed
4. Observe phase-accurate contractions

---

### EEG Brain Signals Visualization
Surface-based electrical signal propagation across the brain.

**Components**:
- 10-20 EEG electrode system mapping
- 60+ electrode positions supported
- Real-time signal amplitude visualization
- Flowing gradient textures

**Technical Details**:
- Electrodes projected onto brain surface using spherical coordinates
- Cell locator ensures paths follow cortical surface
- Region-specific activity thresholds (frontal/central/posterior)
- Bright, animated flow textures

**Usage**:
1. From Brain System, click "EEG Brain Signals"
2. Load EEG data (.edf format)
3. Watch electrical signals flow across brain surface
4. Active paths indicate strong electrode coupling

---

### Anatomically Accurate Coloring

Each system uses medically accurate color schemes:

**Heart**:
- Myocardium: Deep burgundy (0.70, 0.17, 0.17)
- Arteries: Bright red (0.90, 0.15, 0.15)
- Veins: Blue (0.20, 0.30, 0.65)
- Valves: Cream white (0.92, 0.88, 0.85)

**Brain**:
- Gray matter: Pinkish gray (0.75, 0.68, 0.70)
- White matter: White/cream (0.95, 0.93, 0.90)
- Cerebellum: Darker pink (0.70, 0.62, 0.65)
- Blood vessels: Red arteries, blue veins

**Leg**:
- Bone: Ivory/cream (0.95, 0.92, 0.88)
- Muscle: Deep red (0.72, 0.26, 0.26)
- Tendons: Beige (0.92, 0.88, 0.82)
- Cartilage: Bluish white (0.85, 0.90, 0.92)

**Dental**:
- Enamel: Pearl white (0.98, 0.97, 0.94)
- Gums: Healthy pink (0.92, 0.60, 0.65)
- Dentin: Yellowish (0.92, 0.88, 0.78)
- Pulp: Red (0.85, 0.35, 0.35)

---


## 💻 Technical Stack

### Core Technologies
- **Python 3.8+**: Main programming language
- **VTK 9.x**: 3D visualization and rendering engine
- **PyQt5**: GUI framework
- **NumPy**: Numerical computations
- **SciPy**: Signal processing and interpolation

### Medical Data Libraries
- **MNE**: EEG/MEG data processing
- **PyDICOM**: DICOM medical imaging
- **NiBabel**: NIfTI neuroimaging format
- **OpenCV**: Image processing for ECG extraction

### Visualization Libraries
- **Matplotlib**: 2D plotting (ECG signals)
- **VisPy**: High-performance 3D graphics (fly-through mode)

### Key VTK Components Used
- `vtkOBJReader`: OBJ file loading
- `vtkPolyDataMapper`: 3D mesh rendering
- `vtkActor`: Scene objects
- `vtkRenderer`: Rendering pipeline
- `vtkPlane`: Clipping plane implementation
- `vtkCellLocator`: Surface projection
- `vtkParametricSpline`: Curved path generation
- `vtkTubeFilter`: Signal path visualization

---

## 📁 File Structure

```
medical-visualization-system/
│
├── src/
│   ├── gui.py                    # Main system selection GUI
│   ├── heart_gui.py              # Cardiovascular system
│   ├── brain_gui.py              # Nervous system
│   ├── legs_gui.py               # Musculoskeletal system
│   ├── teeth_gui.py              # Dental system
│   ├── Heart_Moving.py           # ECG heart animation
│   ├── moving_stuff.py           # EEG brain signals
│   ├── flyThrough2.py            # Fly-through navigation
│   ├── clippingPlanes.py         # Orthogonal plane viewer
│   └── curvedMPR.py              # Curved MPR generator
│
├── data/
│   ├── heart/                    # Heart 3D models (.obj)
│   ├── brain/                    # Brain 3D models (.obj)
│   ├── leg/                      # Leg 3D models (.obj)
│   └── dental/                   # Dental 3D models (.obj)
│
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## 📦 Requirements

### Hardware Requirements
- **Minimum**:
  - CPU: Dual-core 2.0 GHz
  - RAM: 4 GB
  - GPU: Integrated graphics with OpenGL 3.3+
  - Storage: 2 GB free space

- **Recommended**:
  - CPU: Quad-core 3.0 GHz+
  - RAM: 8 GB+
  - GPU: Dedicated graphics with 2GB VRAM
  - Storage: 10 GB free space (for medical datasets)

### Software Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **OpenGL**: 3.3 or higher


---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

---

## 📄 License

This project is provided as-is for educational purposes. Not intended for clinical diagnostic use.

---

## 🙏 Acknowledgments

- **VTK Community**: For the powerful 3D visualization library
- **MNE Developers**: For EEG/MEG processing tools
- **Medical Dataset Providers**: Open-source anatomical models
- **Research Contributors**: Dr. [Name], Dr. [Name] for validation

---

## 📧 Contact

**Project Contributer**: Radwa Hamdy
- Email: radwahamdy922@gmail.com
- [GitHub](https://github.com/RadwaHa)
- [LinkedIn](https://linkedin.com/in/radwa-hamdy1)

**Project Contributer**:
- Email:
- [GitHub]()
- [LinkedIn]()

**Project Contributer**:
- Email:
- [GitHub]()
- [LinkedIn]()

**Project Contributer**:
- Email:
- [GitHub]()
- [LinkedIn]()

---

**⭐ If you find this project helpful, please consider giving it a star!**

*Last Updated: November 2024*
