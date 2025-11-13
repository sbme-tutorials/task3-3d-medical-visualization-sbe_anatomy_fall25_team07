"""
Professional 3D Heart Blood Flow Visualization with Separate Chambers
Smooth, realistic animation using anatomically accurate chamber models

Required packages:
pip install vtk PyQt5 numpy scipy matplotlib pillow opencv-python
"""

import sys
import os
import numpy as np
import vtk
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QGroupBox, 
                             QSlider, QTextEdit)
from PyQt5.QtCore import QTimer, Qt
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from scipy import signal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import glob

# ==================== ECG Processing ====================
def load_ecg_data(ecg_folder_path):
    """Load ECG from PNG images with improved extraction"""
    try:
        import cv2
    except ImportError:
        return None, None
    
    ecg_files = []
    for pattern in ['*.png', '*.PNG', '*.jpg', '*.JPG']:
        ecg_files.extend(glob.glob(os.path.join(ecg_folder_path, pattern)))
    
    if not ecg_files:
        for root, dirs, files in os.walk(ecg_folder_path):
            for pattern in ['*.png', '*.PNG']:
                ecg_files.extend(glob.glob(os.path.join(root, pattern)))
    
    if not ecg_files:
        return None, None
    
    try:
        # Load image
        img = cv2.imread(ecg_files[0], cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None, None
        
        print(f"Image size: {img.shape}")
        
        # Improved ECG extraction: find the actual signal line
        height, width = img.shape
        ecg_signal = np.zeros(width)
        
        # For each column, find the darkest pixels (the ECG line)
        for col in range(width):
            column_pixels = img[:, col]
            
            # Find pixels below threshold (darker = signal)
            threshold = np.mean(column_pixels) - 0.5 * np.std(column_pixels)
            dark_pixels = np.where(column_pixels < threshold)[0]
            
            if len(dark_pixels) > 0:
                # Use the median position of dark pixels as the signal
                signal_position = np.median(dark_pixels)
                # Invert so peak upward corresponds to higher values
                ecg_signal[col] = height - signal_position
            else:
                # No signal detected, use middle
                ecg_signal[col] = height / 2
        
        # Normalize
        ecg_signal = (ecg_signal - np.min(ecg_signal)) / (np.max(ecg_signal) - np.min(ecg_signal))
        
        # Center around zero and scale
        ecg_signal = (ecg_signal - 0.5) * 2
        
        # Apply smoothing to reduce noise
        from scipy.ndimage import gaussian_filter1d
        ecg_signal = gaussian_filter1d(ecg_signal, sigma=1.5)
        
        # Normalize again to standard ECG range
        ecg_signal = (ecg_signal - np.mean(ecg_signal)) / np.std(ecg_signal)
        
        # Resample if needed for better resolution
        if len(ecg_signal) < 2000:
            from scipy.interpolate import interp1d
            x_old = np.linspace(0, 1, len(ecg_signal))
            x_new = np.linspace(0, 1, 3600)
            f = interp1d(x_old, ecg_signal, kind='cubic')
            ecg_signal = f(x_new)
        
        sampling_rate = 360
        duration = len(ecg_signal) / sampling_rate
        time = np.linspace(0, duration, len(ecg_signal))
        
        print(f"✓ ECG extracted: {duration:.1f}s, {len(ecg_signal)} samples")
        return time, ecg_signal
    
    except Exception as e:
        print(f"Error extracting ECG: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def generate_synthetic_ecg(duration=10, sampling_rate=360):
    """Generate synthetic ECG"""
    t = np.linspace(0, duration, int(duration * sampling_rate))
    heart_rate = 75
    beat_interval = 60 / heart_rate
    ecg = np.zeros_like(t)
    
    num_beats = int(duration / beat_interval)
    for beat in range(num_beats):
        t_beat = beat * beat_interval
        ecg += 0.15 * np.exp(-((t - t_beat) ** 2) / (2 * (0.08 / 4) ** 2))
        qrs_time = t_beat + 0.16
        ecg += -0.05 * np.exp(-((t - (qrs_time - 0.02)) ** 2) / (2 * (0.02 / 4) ** 2))
        ecg += 1.0 * np.exp(-((t - qrs_time) ** 2) / (2 * (0.03 / 4) ** 2))
        ecg += -0.1 * np.exp(-((t - (qrs_time + 0.03)) ** 2) / (2 * (0.02 / 4) ** 2))
        t_wave_time = t_beat + 0.40
        ecg += 0.3 * np.exp(-((t - t_wave_time) ** 2) / (2 * (0.12 / 4) ** 2))
    
    ecg += np.random.normal(0, 0.02, len(ecg))
    return t, ecg

def detect_ecg_features(t, ecg, sampling_rate=360):
    """Detect ECG features"""
    features = {'p_waves': [], 'qrs_complexes': [], 't_waves': []}
    
    peaks, _ = signal.find_peaks(ecg, height=np.mean(ecg) + 0.3 * np.std(ecg), 
                                 distance=int(0.5 * sampling_rate))
    features['qrs_complexes'] = t[peaks]
    
    for qrs_time in features['qrs_complexes']:
        p_mask = (t >= max(0, qrs_time - 0.2)) & (t < qrs_time - 0.1)
        if np.any(p_mask):
            features['p_waves'].append(t[p_mask][np.argmax(ecg[p_mask])])
        
        t_mask = (t >= qrs_time + 0.15) & (t < qrs_time + 0.5)
        if np.any(t_mask):
            features['t_waves'].append(t[t_mask][np.argmax(ecg[t_mask])])
    
    return features

def get_cardiac_phase(current_time, features):
    """Determine cardiac phase with accurate timing for each chamber"""
    qrs_times = np.array(features['qrs_complexes'])
    if len(qrs_times) == 0:
        return 'diastole', 0.0, 0.0, 0.0, 0.0
    
    closest_qrs_idx = np.argmin(np.abs(qrs_times - current_time))
    qrs_time = qrs_times[closest_qrs_idx]
    time_in_cycle = current_time - qrs_time
    
    # Initialize progress for each chamber
    ra_progress = 0.0  # Right atrium
    la_progress = 0.0  # Left atrium
    rv_progress = 0.0  # Right ventricle
    lv_progress = 0.0  # Left ventricle
    
    phase = 'diastole'
    
    # Atrial systole: RA starts first, LA follows ~30ms later
    if -0.18 < time_in_cycle < -0.05:
        phase = 'atrial_systole'
        # Right atrium: starts at -0.18, peaks at -0.11
        if -0.18 < time_in_cycle < -0.08:
            ra_progress = (time_in_cycle + 0.18) / 0.10
        elif -0.08 <= time_in_cycle < -0.05:
            ra_progress = 1.0 - (time_in_cycle + 0.08) / 0.03
        else:
            ra_progress = 0.0
        
        # Left atrium: starts ~30ms after RA (-0.15), peaks at -0.08
        if -0.15 < time_in_cycle < -0.05:
            if -0.15 < time_in_cycle < -0.08:
                la_progress = (time_in_cycle + 0.15) / 0.07
            else:
                la_progress = 1.0 - (time_in_cycle + 0.08) / 0.03
        else:
            la_progress = 0.0
    
    # Ventricular systole: Both ventricles contract almost simultaneously
    elif -0.05 <= time_in_cycle <= 0.22:
        phase = 'ventricular_systole'
        # Right ventricle: starts slightly before LV
        if -0.05 <= time_in_cycle <= 0.20:
            if time_in_cycle < 0.08:
                rv_progress = (time_in_cycle + 0.05) / 0.13
            else:
                rv_progress = 1.0 - (time_in_cycle - 0.08) / 0.12
        else:
            rv_progress = 0.0
        
        # Left ventricle: starts ~10ms after RV
        if -0.04 <= time_in_cycle <= 0.22:
            if time_in_cycle < 0.09:
                lv_progress = (time_in_cycle + 0.04) / 0.13
            else:
                lv_progress = 1.0 - (time_in_cycle - 0.09) / 0.13
        else:
            lv_progress = 0.0
    
    else:
        # Diastole: all chambers relaxed
        phase = 'diastole'
        ra_progress = 0.0
        la_progress = 0.0
        rv_progress = 0.0
        lv_progress = 0.0
    
    return phase, ra_progress, la_progress, rv_progress, lv_progress

# ==================== Chamber Management ====================
def load_chamber_files(heart_folder):
    """Load separate chamber OBJ files"""
    chambers = {
        'right_atrium': [],
        'left_atrium': [],
        'right_ventricle': [],
        'left_ventricle': []
    }
    
    # Right Atrium files
    ra_patterns = ['MM559_*', 'MM560_*', 'MM590_*', 'MM461_*', 'MM462_*', 'MM463_*']
    # Left Atrium files  
    la_patterns = ['MM456_*', 'MM458_*', 'MM460_*', 'MM632_*', 'MM633_*', 'MM459_*']
    # Right Ventricle files
    rv_patterns = ['MM538_*', 'MM598_*', 'MM564_*', 'MM532_*', 'MM537_*', 'MM550_*', 'MM551_*']
    # Left Ventricle files
    lv_patterns = ['MM474_*', 'MM613_*', 'MM614_*', 'MM615_*', 'MM616_*', 'MM618_*', 
                   'MM620_*', 'MM621_*', 'MM622_*', 'MM623_*', 'MM624_*', 'MM625_*',
                   'MM626_*', 'MM627_*', 'MM628_*', 'MM629_*', 'MM631_*', 'MM599_*',
                   'MM636_*', 'MM637_*']
    
    for pattern in ra_patterns:
        chambers['right_atrium'].extend(glob.glob(os.path.join(heart_folder, pattern + '.obj')))
    
    for pattern in la_patterns:
        chambers['left_atrium'].extend(glob.glob(os.path.join(heart_folder, pattern + '.obj')))
    
    for pattern in rv_patterns:
        chambers['right_ventricle'].extend(glob.glob(os.path.join(heart_folder, pattern + '.obj')))
    
    for pattern in lv_patterns:
        chambers['left_ventricle'].extend(glob.glob(os.path.join(heart_folder, pattern + '.obj')))
    
    return chambers

def create_chamber_actor(file_paths, color, opacity):
    """Create combined actor from multiple OBJ files"""
    if not file_paths:
        return None
    
    append_filter = vtk.vtkAppendPolyData()
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            continue
        
        reader = vtk.vtkOBJReader()
        reader.SetFileName(file_path)
        reader.Update()
        append_filter.AddInputData(reader.GetOutput())
    
    append_filter.Update()
    
    # Store original for deformation
    original_polydata = vtk.vtkPolyData()
    original_polydata.DeepCopy(append_filter.GetOutput())
    
    deformed_polydata = vtk.vtkPolyData()
    deformed_polydata.DeepCopy(original_polydata)
    
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(deformed_polydata)
    
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(color)
    actor.GetProperty().SetOpacity(opacity)
    actor.GetProperty().SetSpecular(0.3)
    
    return actor, original_polydata, deformed_polydata

def deform_chamber(original_polydata, deformed_polydata, contraction_factor):
    """Apply smooth wall-thickening contraction (not moving toward center)"""
    points = original_polydata.GetPoints()
    num_points = points.GetNumberOfPoints()
    
    if num_points == 0:
        return
    
    bounds = original_polydata.GetBounds()
    center_x = (bounds[0] + bounds[1]) / 2
    center_y = (bounds[2] + bounds[3]) / 2
    center_z = (bounds[4] + bounds[5]) / 2
    
    new_points = vtk.vtkPoints()
    new_points.SetNumberOfPoints(num_points)
    
    for i in range(num_points):
        x, y, z = points.GetPoint(i)
        
        # Vector from center to point
        dx = x - center_x
        dy = y - center_y
        dz = z - center_z
        distance = np.sqrt(dx*dx + dy*dy + dz*dz)
        
        if distance > 0.001:  # Avoid division by zero
            # Calculate how much this point should move inward
            # Only move inward from the outer surface (wall thickening effect)
            # Use a non-linear scale to keep outer shape more stable
            
            # Points closer to center move less (preserve internal structure)
            # Points on outer wall move more (chamber volume reduces)
            relative_distance = min(1.0, distance / 3.0)  # Normalize distance
            
            # Scale factor: outer points contract more, inner points barely move
            point_scale = 1.0 - (1.0 - contraction_factor) * relative_distance
            
            new_x = center_x + dx * point_scale
            new_y = center_y + dy * point_scale
            new_z = center_z + dz * point_scale
        else:
            new_x, new_y, new_z = x, y, z
        
        new_points.SetPoint(i, new_x, new_y, new_z)
    
    deformed_polydata.SetPoints(new_points)
    deformed_polydata.Modified()

# ==================== Blood Flow ====================
def create_blood_flow(renderer, phase, progress, chamber_positions):
    """Create realistic blood flow"""
    actors = []
    
    if phase == 'atrial_systole':
        paths = [
            {'start': (2, 2.5, 1), 'end': (2, -0.5, -1), 'color': (0.7, 0, 0.1), 'n': 80, 'size': 0.16},
            {'start': (-2, 2.5, 1), 'end': (-2, -0.5, -1.5), 'color': (1, 0, 0), 'n': 80, 'size': 0.16},
        ]
    elif phase == 'ventricular_systole':
        paths = [
            {'start': (2, 0, -1), 'end': (2, -2, -4), 'color': (0.7, 0, 0.1), 'n': 100, 'size': 0.14},
            {'start': (-2, 0, -1.5), 'end': (-2, -2, -5), 'color': (1, 0, 0), 'n': 100, 'size': 0.16},
        ]
    else:
        paths = [
            {'start': (2, 3.5, 2), 'end': (2, 2, 0.5), 'color': (0.5, 0, 0.4), 'n': 60, 'size': 0.14},
            {'start': (-2, 3.5, 2), 'end': (-2, 2, 0.5), 'color': (1, 0, 0), 'n': 60, 'size': 0.14},
            {'start': (2, 1.5, 0), 'end': (2, -0.5, -1.5), 'color': (0.7, 0, 0.1), 'n': 50, 'size': 0.12},
            {'start': (-2, 1.5, 0), 'end': (-2, -0.5, -2), 'color': (1, 0.1, 0), 'n': 50, 'size': 0.12},
        ]
    
    for path in paths:
        for i in range(path['n']):
            t = (i / path['n'] + progress * 0.7) % 1.0
            pos = np.array(path['start']) * (1 - t) + np.array(path['end']) * t
            pos += np.random.normal(0, 0.3 * (1 - abs(t - 0.5)), 3)
            
            size = path['size'] * (0.8 + 0.4 * np.sin(t * 4 * np.pi))
            
            sphere = vtk.vtkSphereSource()
            sphere.SetRadius(size)
            sphere.SetCenter(pos[0], pos[1], pos[2])
            sphere.SetPhiResolution(16)
            sphere.SetThetaResolution(16)
            
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(sphere.GetOutputPort())
            
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(path['color'])
            actor.GetProperty().SetOpacity(0.92)
            actor.GetProperty().SetSpecular(0.9)
            actor.GetProperty().SetSpecularPower(50)
            actor.GetProperty().SetAmbient(0.4)
            
            renderer.AddActor(actor)
            actors.append(actor)
    
    return actors

# ==================== Main Application ====================
class HeartVisualizationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Professional Heart Visualization with Separate Chambers")
        self.setGeometry(100, 100, 1600, 900)
        
        self.ecg_time = None
        self.ecg_signal = None
        self.ecg_features = None
        self.current_time = 0.0
        self.is_playing = False
        self.blood_actors = []
        
        # Chamber data structures
        self.chambers = {}
        
        self.setup_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_visualization)
        
    def setup_ui(self):
        """Setup UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMinimumWidth(380)  # Wider to accommodate longest text
        left_panel.setMaximumWidth(380)  # Fixed width prevents resizing
        
        # Status
        file_group = QGroupBox("Data Status")
        file_layout = QVBoxLayout()
        
        self.model_path_label = QLabel("Loading...")
        self.model_path_label.setWordWrap(True)
        self.ecg_path_label = QLabel("Loading...")
        self.ecg_path_label.setWordWrap(True)
        
        file_layout.addWidget(QLabel("Heart Chambers:"))
        file_layout.addWidget(self.model_path_label)
        file_layout.addWidget(QLabel("ECG Data:"))
        file_layout.addWidget(self.ecg_path_label)
        file_group.setLayout(file_layout)
        
        # Controls
        playback_group = QGroupBox("Playback")
        playback_layout = QVBoxLayout()
        
        self.play_pause_btn = QPushButton("▶ Play")
        self.play_pause_btn.clicked.connect(self.toggle_playback)
        self.play_pause_btn.setEnabled(False)
        
        self.reset_btn = QPushButton("⟲ Reset")
        self.reset_btn.clicked.connect(self.reset_visualization)
        self.reset_btn.setEnabled(False)
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(10)
        self.speed_slider.setValue(5)  # Default to 1.0x speed
        self.speed_value_label = QLabel("Speed: 1.0x")
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        
        playback_layout.addWidget(self.play_pause_btn)
        playback_layout.addWidget(self.reset_btn)
        playback_layout.addWidget(QLabel("Speed:"))
        playback_layout.addWidget(self.speed_slider)
        playback_layout.addWidget(self.speed_value_label)
        playback_group.setLayout(playback_layout)
        
        # Phase
        phase_group = QGroupBox("Cardiac Phase")
        phase_layout = QVBoxLayout()
        self.phase_label = QLabel("---")
        self.phase_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.phase_label.setAlignment(Qt.AlignCenter)
        self.phase_label.setMinimumHeight(60)  # Fixed height for phase name
        self.phase_desc = QLabel("")
        self.phase_desc.setWordWrap(True)
        self.phase_desc.setAlignment(Qt.AlignCenter)
        self.phase_desc.setMinimumHeight(80)  # Fixed height for description
        self.phase_desc.setMaximumHeight(80)
        phase_layout.addWidget(self.phase_label)
        phase_layout.addWidget(self.phase_desc)
        phase_group.setLayout(phase_layout)
        
        # Status
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(180)
        status_layout.addWidget(self.status_text)
        status_group.setLayout(status_layout)
        
        left_layout.addWidget(file_group)
        left_layout.addWidget(playback_group)
        left_layout.addWidget(phase_group)
        left_layout.addWidget(status_group)
        left_layout.addStretch()
        
        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # VTK
        self.vtk_widget = QVTKRenderWindowInteractor(right_panel)
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.02, 0.02, 0.08)
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        
        self.setup_camera()
        
        # ECG
        self.figure, self.ax_ecg = plt.subplots(figsize=(10, 2))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMaximumHeight(200)
        
        right_layout.addWidget(self.vtk_widget, stretch=3)
        right_layout.addWidget(self.canvas, stretch=1)
        
        main_layout.addWidget(left_panel, stretch=1)
        main_layout.addWidget(right_panel, stretch=5)
        
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()
    
    def setup_camera(self):
        """Setup camera"""
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(10, 5, 10)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1)
        
        for pos, intensity in [((12, 12, 12), 1.0), ((-10, 6, 10), 0.6), ((0, -6, 8), 0.4)]:
            light = vtk.vtkLight()
            light.SetPosition(pos)
            light.SetFocalPoint(0, 0, 0)
            light.SetIntensity(intensity)
            self.renderer.AddLight(light)
    
    def load_heart_chambers(self, heart_folder):
        """Load separate chamber files"""
        try:
            self.status_text.append("Loading heart chambers...")
            chamber_files = load_chamber_files(heart_folder)
            
            # Create actors for each chamber
            ra_result = create_chamber_actor(chamber_files['right_atrium'], (0.95, 0.7, 0.7), 0.25)
            la_result = create_chamber_actor(chamber_files['left_atrium'], (0.95, 0.75, 0.75), 0.25)
            rv_result = create_chamber_actor(chamber_files['right_ventricle'], (0.9, 0.65, 0.65), 0.25)
            lv_result = create_chamber_actor(chamber_files['left_ventricle'], (0.9, 0.7, 0.7), 0.25)
            
            if ra_result:
                self.chambers['RA'] = {'actor': ra_result[0], 'original': ra_result[1], 'deformed': ra_result[2]}
                self.renderer.AddActor(ra_result[0])
                self.status_text.append(f"✓ Right Atrium: {len(chamber_files['right_atrium'])} files")
            
            if la_result:
                self.chambers['LA'] = {'actor': la_result[0], 'original': la_result[1], 'deformed': la_result[2]}
                self.renderer.AddActor(la_result[0])
                self.status_text.append(f"✓ Left Atrium: {len(chamber_files['left_atrium'])} files")
            
            if rv_result:
                self.chambers['RV'] = {'actor': rv_result[0], 'original': rv_result[1], 'deformed': rv_result[2]}
                self.renderer.AddActor(rv_result[0])
                self.status_text.append(f"✓ Right Ventricle: {len(chamber_files['right_ventricle'])} files")
            
            if lv_result:
                self.chambers['LV'] = {'actor': lv_result[0], 'original': lv_result[1], 'deformed': lv_result[2]}
                self.renderer.AddActor(lv_result[0])
                self.status_text.append(f"✓ Left Ventricle: {len(chamber_files['left_ventricle'])} files")
            
            self.renderer.ResetCamera()
            self.vtk_widget.GetRenderWindow().Render()
            
            self.model_path_label.setText(f"✓ {len(self.chambers)} chambers loaded")
            self.model_path_label.setStyleSheet("color: green;")
            
            self.check_ready_state()
            
        except Exception as e:
            self.status_text.append(f"✗ Error: {str(e)}")
            self.model_path_label.setText("❌ Load failed")
            self.model_path_label.setStyleSheet("color: red;")
    
    def load_ecg(self, folder_path):
        """Load ECG"""
        self.status_text.append("Loading ECG...")
        time, signal_data = load_ecg_data(folder_path)
        
        if time is not None:
            self.ecg_time = time
            self.ecg_signal = signal_data
            self.ecg_features = detect_ecg_features(time, signal_data)
            
            self.ecg_path_label.setText("✓ Real ECG data")
            self.ecg_path_label.setStyleSheet("color: green;")
            self.status_text.append(f"✓ ECG: {len(self.ecg_features['qrs_complexes'])} beats")
            
            self.plot_ecg()
            self.check_ready_state()
        else:
            self.status_text.append("Using synthetic ECG")
            self.use_synthetic_ecg()
    
    def use_synthetic_ecg(self):
        """Use synthetic ECG"""
        time, signal_data = generate_synthetic_ecg(duration=10)
        self.ecg_time = time
        self.ecg_signal = signal_data
        self.ecg_features = detect_ecg_features(time, signal_data)
        
        self.ecg_path_label.setText("✓ Synthetic")
        self.ecg_path_label.setStyleSheet("color: orange;")
        
        self.plot_ecg()
        self.check_ready_state()
    
    def plot_ecg(self):
        """Plot ECG"""
        self.ax_ecg.clear()
        self.ax_ecg.plot(self.ecg_time, self.ecg_signal, 'b-', linewidth=1.5)
        self.ax_ecg.set_xlabel('Time (s)')
        self.ax_ecg.set_ylabel('Amplitude')
        self.ax_ecg.set_title('ECG Signal')
        self.ax_ecg.grid(True, alpha=0.3)
        
        self.time_marker = self.ax_ecg.axvline(x=0, color='red', linewidth=2)
        self.canvas.draw()
    
    def check_ready_state(self):
        """Check if ready"""
        if self.ecg_time is not None and self.chambers:
            self.play_pause_btn.setEnabled(True)
            self.reset_btn.setEnabled(True)
            self.status_text.append("✓ Ready to play!")
    
    def toggle_playback(self):
        """Toggle playback"""
        if not self.is_playing:
            self.is_playing = True
            self.play_pause_btn.setText("⏸ Pause")
            speed = self.speed_slider.value() / 5.0
            self.timer.start(int(50 / speed))
        else:
            self.is_playing = False
            self.play_pause_btn.setText("▶ Play")
            self.timer.stop()
    
    def reset_visualization(self):
        """Reset"""
        self.current_time = 0.0
        self.is_playing = False
        self.play_pause_btn.setText("▶ Play")
        self.timer.stop()
        self.update_visualization()
    
    def update_speed_label(self):
        """Update speed"""
        speed = self.speed_slider.value() / 5.0
        self.speed_value_label.setText(f"Speed: {speed:.1f}x")
    
    def update_visualization(self):
        """Update visualization"""
        if self.ecg_time is None or not self.chambers:
            return
        
        speed = self.speed_slider.value() / 5.0
        self.current_time += 0.05 * speed
        
        if self.current_time > self.ecg_time[-1]:
            self.current_time = 0.0
        
        self.time_marker.set_xdata([self.current_time, self.current_time])
        self.canvas.draw()
        
        phase, progress = get_cardiac_phase(self.current_time, self.ecg_features)
        
        phase_info = {
            'atrial_systole': ('ATRIAL SYSTOLE', 'Atria squeeze\nVentricles fill', '#FF8C00'),
            'ventricular_systole': ('VENTRICULAR SYSTOLE', 'Ventricles squeeze\nAtria fill', '#DC143C'),
            'diastole': ('DIASTOLE', 'All chambers relax\nPassive filling', '#4169E1')
        }
        
        name, desc, color = phase_info.get(phase, ('', '', 'black'))
        self.phase_label.setText(name)
        self.phase_desc.setText(desc)
        self.phase_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        
    def update_visualization(self):
        """Update visualization with sequential chamber contraction"""
        if self.ecg_time is None or not self.chambers:
            return
        
        speed = self.speed_slider.value() / 5.0
        self.current_time += 0.05 * speed
        
        if self.current_time > self.ecg_time[-1]:
            self.current_time = 0.0
        
        self.time_marker.set_xdata([self.current_time, self.current_time])
        self.canvas.draw()
        
        # Get individual chamber progress
        phase, ra_prog, la_prog, rv_prog, lv_prog = get_cardiac_phase(self.current_time, self.ecg_features)
        
        phase_info = {
            'atrial_systole': ('ATRIAL SYSTOLE', 'RA→LA sequential\nFilling ventricles', '#FF8C00'),
            'ventricular_systole': ('VENTRICULAR SYSTOLE', 'RV→LV contraction\nEjecting blood', '#DC143C'),
            'diastole': ('DIASTOLE', 'All chambers relax\nPassive filling', '#4169E1')
        }
        
        name, desc, color = phase_info.get(phase, ('', '', 'black'))
        self.phase_label.setText(name)
        self.phase_desc.setText(desc)
        self.phase_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        
        # Calculate individual chamber contraction factors
        # Use subtle contraction to maintain unified heart appearance
        # Atria: gentle wall thickening (subtle chamber volume reduction)
        ra_factor = 1.0 - 0.06 * ra_prog  # RA: 1.0 → 0.94 (subtle)
        la_factor = 1.0 - 0.06 * la_prog  # LA: 1.0 → 0.94 (subtle)
        
        # Ventricles: visible but not dramatic wall thickening
        rv_factor = 1.0 - 0.15 * rv_prog  # RV: 1.0 → 0.85 (visible)
        lv_factor = 1.0 - 0.15 * lv_prog  # LV: 1.0 → 0.85 (visible)
        
        # Apply deformations to each chamber independently
        if 'RA' in self.chambers:
            deform_chamber(self.chambers['RA']['original'], self.chambers['RA']['deformed'], ra_factor)
        if 'LA' in self.chambers:
            deform_chamber(self.chambers['LA']['original'], self.chambers['LA']['deformed'], la_factor)
        if 'RV' in self.chambers:
            deform_chamber(self.chambers['RV']['original'], self.chambers['RV']['deformed'], rv_factor)
        if 'LV' in self.chambers:
            deform_chamber(self.chambers['LV']['original'], self.chambers['LV']['deformed'], lv_factor)
        
        # Update blood flow based on overall phase
        for actor in self.blood_actors:
            self.renderer.RemoveActor(actor)
        self.blood_actors.clear()
        
        # Use max progress for blood flow animation
        overall_progress = max(ra_prog, la_prog, rv_prog, lv_prog)
        chamber_positions = {}
        self.blood_actors = create_blood_flow(self.renderer, phase, overall_progress, chamber_positions)
        
        self.vtk_widget.GetRenderWindow().Render()


def main():
    # ========== CONFIGURE YOUR PATHS HERE ==========
    HEART_MODEL_FOLDER = r"C:\Users\Galaxy\Downloads\Heart\Heart 3D"
    ECG_FOLDER_PATH = r"C:\Users\Galaxy\Downloads\Heart\Normal Person"
    # ===============================================
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = HeartVisualizationApp()
    
    # Load heart chambers
    if HEART_MODEL_FOLDER and os.path.exists(HEART_MODEL_FOLDER):
        print(f"Loading heart chambers from: {HEART_MODEL_FOLDER}")
        window.load_heart_chambers(HEART_MODEL_FOLDER)
    else:
        print(f"⚠ Heart model folder not found")
        window.model_path_label.setText("❌ Folder not found")
        window.model_path_label.setStyleSheet("color: red;")
    
    # Load ECG data
    if ECG_FOLDER_PATH and os.path.exists(ECG_FOLDER_PATH):
        print(f"Loading ECG from: {ECG_FOLDER_PATH}")
        window.load_ecg(ECG_FOLDER_PATH)
    else:
        print(f"⚠ ECG folder not found, using synthetic")
        window.use_synthetic_ecg()
    
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()