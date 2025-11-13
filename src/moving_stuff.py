"""
Nervous System - Realistic EEG Electrical Signal Visualization
SURFACE-BASED VERSION - Paths directly on brain surface

Features:
- Paths placed directly ON brain surface (not floating above)
- Straight/gently curved connections (not highly arced)
- Realistic brain-based signal propagation
- EEG data-driven electrical flows
"""
import os
import sys
import numpy as np
import vtk
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QSlider, QCheckBox,
                             QLabel, QFrame)
from PyQt5.QtCore import Qt, QTimer
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

try:
    import mne
    MNE_AVAILABLE = True
except ImportError:
    MNE_AVAILABLE = False
    print("⚠ Install MNE: pip install mne")

try:
    from scipy.ndimage import gaussian_filter1d
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("⚠ Install scipy: pip install scipy")

# Extended 10-20 EEG electrode positions (spherical coordinates)
# Including 10-10 and 10-5 system electrodes
ELECTRODE_POSITIONS_10_20 = {
    # Frontal pole
    'FP1': (-25, 75, 1.0), 'FP2': (25, 75, 1.0), 'FPZ': (0, 80, 1.0),
    
    # Frontal
    'F7': (-60, 45, 1.0), 'F5': (-45, 50, 1.0), 'F3': (-30, 55, 1.0), 
    'F1': (-15, 60, 1.0), 'FZ': (0, 65, 1.0), 'F2': (15, 60, 1.0),
    'F4': (30, 55, 1.0), 'F6': (45, 50, 1.0), 'F8': (60, 45, 1.0),
    
    # Anterior frontal
    'AF7': (-55, 60, 1.0), 'AF3': (-30, 65, 1.0), 'AFZ': (0, 70, 1.0),
    'AF4': (30, 65, 1.0), 'AF8': (55, 60, 1.0),
    
    # Fronto-central
    'FC5': (-55, 30, 1.0), 'FC3': (-35, 35, 1.0), 'FC1': (-18, 40, 1.0),
    'FCZ': (0, 45, 1.0), 'FC2': (18, 40, 1.0), 'FC4': (35, 35, 1.0),
    'FC6': (55, 30, 1.0),
    
    # Fronto-temporal
    'FT7': (-70, 20, 1.0), 'FT8': (70, 20, 1.0),
    
    # Central
    'C5': (-60, 0, 1.0), 'C3': (-45, 0, 1.0), 'C1': (-22, 0, 1.0),
    'CZ': (0, 0, 1.0), 'C2': (22, 0, 1.0), 'C4': (45, 0, 1.0),
    'C6': (60, 0, 1.0),
    
    # Temporal
    'T7': (-90, 0, 1.0), 'T9': (-110, 0, 0.95), 'T8': (90, 0, 1.0),
    'T10': (110, 0, 0.95), 'T3': (-75, -15, 1.0), 'T4': (75, -15, 1.0),
    'T5': (-75, -45, 1.0), 'T6': (75, -45, 1.0),
    
    # Centro-parietal
    'CP5': (-55, -30, 1.0), 'CP3': (-35, -35, 1.0), 'CP1': (-18, -40, 1.0),
    'CPZ': (0, -45, 1.0), 'CP2': (18, -40, 1.0), 'CP4': (35, -35, 1.0),
    'CP6': (55, -30, 1.0),
    
    # Temporo-parietal
    'TP7': (-70, -40, 1.0), 'TP8': (70, -40, 1.0),
    
    # Parietal
    'P7': (-60, -50, 1.0), 'P5': (-45, -50, 1.0), 'P3': (-30, -55, 1.0),
    'P1': (-15, -60, 1.0), 'PZ': (0, -65, 1.0), 'P2': (15, -60, 1.0),
    'P4': (30, -55, 1.0), 'P6': (45, -50, 1.0), 'P8': (60, -50, 1.0),
    
    # Parieto-occipital
    'PO7': (-55, -65, 1.0), 'PO3': (-30, -70, 1.0), 'POZ': (0, -75, 1.0),
    'PO4': (30, -70, 1.0), 'PO8': (55, -65, 1.0),
    
    # Occipital
    'O1': (-20, -80, 1.0), 'OZ': (0, -85, 1.0), 'O2': (20, -80, 1.0),
    
    # Inion
    'IZ': (0, -90, 0.95),
}

def spherical_to_cartesian(theta_deg, phi_deg, r, center, scale):
    """Convert spherical to Cartesian coordinates"""
    theta = np.radians(theta_deg)
    phi = np.radians(phi_deg)
    x = r * np.cos(phi) * np.sin(theta)
    y = r * np.cos(phi) * np.cos(theta)
    z = r * np.sin(phi)
    return center + np.array([x, y, z]) * scale


class BrainEEGVisualizerApp(QMainWindow):
    def __init__(self, model_folder, edf_path):
        super().__init__()
        self.setWindowTitle("⚡ Brain EEG - Surface Electrical Signals")
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet("background-color: #1a1a1a; color: white;")

        self.model_folder = model_folder
        self.edf_path = edf_path
        self.is_playing = True
        self.speed = 0.5
        self.intensity = 3.0
        self.current_frame = 0
        
        self._load_eeg_data()
        
        # Setup UI
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        
        self._create_control_panel()
        self._setup_vtk_scene()
        
        self.main_layout.addWidget(self.control_panel, 1)
        self.main_layout.addWidget(self.vtkWidget, 4)
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animation_loop)
        self.timer.start(33)

    def _load_eeg_data(self):
        """Load and preprocess EEG data"""
        print(f"\n{'='*70}")
        print("LOADING EEG DATA")
        print(f"{'='*70}")
        print(f"✓ Loading from: {self.edf_path}")
        
        raw = mne.io.read_raw_edf(self.edf_path, preload=True, verbose=False)
        data, self.ch_names = raw.get_data(), raw.ch_names
        self.sfreq = int(raw.info["sfreq"])
        self.n_samples = data.shape[1]
        
        print(f"  Sampling rate: {self.sfreq} Hz")
        print(f"  Duration: {self.n_samples/self.sfreq:.1f}s")
        print(f"  Channels: {len(self.ch_names)}")
        
        # Normalize data
        data_norm = np.zeros_like(data)
        for i in range(len(self.ch_names)):
            channel_data = data[i, :]
            data_std = np.std(channel_data)
            if data_std > 0:
                data_norm[i, :] = np.abs((channel_data - np.mean(channel_data)) / data_std)
        
        if SCIPY_AVAILABLE:
            data_norm = gaussian_filter1d(data_norm, sigma=10, axis=1)
        
        max_val = np.percentile(data_norm, 95)
        self.data_normalized = np.clip(data_norm / max_val, 0, 1)
        print(f"✓ EEG data loaded and normalized")

    def _create_control_panel(self):
        """Create GUI control panel"""
        self.control_panel = QFrame()
        self.control_panel.setStyleSheet("""
            QFrame { background-color: #2b2b2b; border-radius: 10px; padding: 15px; }
            QPushButton { background-color: #4CAF50; color: white; border: none; 
                         padding: 12px; font-size: 14px; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #45a049; }
            QLabel { color: #00ff88; font-size: 12px; font-weight: bold; margin-top: 10px; }
            QSlider::groove:horizontal { background: #3b3b3b; height: 8px; border-radius: 4px; }
            QSlider::handle:horizontal { background: #00ff88; width: 18px; 
                                        height: 18px; margin: -5px 0; border-radius: 9px; }
        """)
        self.control_panel.setFixedWidth(380)
        
        panel_layout = QVBoxLayout(self.control_panel)
        
        # Title
        title = QLabel("⚡ Brain EEG Control Panel")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00ff88; margin-bottom: 20px;")
        panel_layout.addWidget(title)
        
        # Playback controls
        playback_label = QLabel("⏯️ PLAYBACK CONTROLS")
        panel_layout.addWidget(playback_label)
        
        self.play_pause_btn = QPushButton("⏸️ Pause")
        self.play_pause_btn.clicked.connect(self._toggle_play_pause)
        
        reset_btn = QPushButton("🔄 Reset")
        reset_btn.setStyleSheet("QPushButton { background-color: #FF9800; }")
        reset_btn.clicked.connect(self._reset_animation)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.play_pause_btn)
        button_layout.addWidget(reset_btn)
        panel_layout.addLayout(button_layout)
        
        # Info display
        info_label = QLabel("ℹ️ INFORMATION")
        panel_layout.addWidget(info_label)
        
        self.info_text = QLabel()
        self.info_text.setStyleSheet("""
            color: #00ff88; background-color: #1b1b1b; 
            padding: 10px; border-radius: 5px; font-size: 10px; font-family: 'Courier New';
        """)
        self.info_text.setWordWrap(True)
        panel_layout.addWidget(self.info_text)
        
        panel_layout.addStretch()

    def _setup_vtk_scene(self):
        """Setup VTK visualization"""
        print(f"\n{'='*70}")
        print("SETTING UP 3D VISUALIZATION")
        print(f"{'='*70}")
        
        # Create VTK widget
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.renderer.SetBackground(0.05, 0.05, 0.1)
        
        # Load and combine brain meshes
        print(f"✓ Loading brain meshes from: {self.model_folder}")
        append_filter = vtk.vtkAppendPolyData()
        mesh_count = 0
        
        for filename in os.listdir(self.model_folder):
            if filename.lower().endswith(('.obj', '.stl', '.ply')):
                filepath = os.path.join(self.model_folder, filename)
                
                if filename.lower().endswith('.obj'):
                    reader = vtk.vtkOBJReader()
                elif filename.lower().endswith('.stl'):
                    reader = vtk.vtkSTLReader()
                elif filename.lower().endswith('.ply'):
                    reader = vtk.vtkPLYReader()
                
                reader.SetFileName(filepath)
                reader.Update()
                append_filter.AddInputData(reader.GetOutput())
                mesh_count += 1
                print(f"  Loaded: {filename}")
        
        append_filter.Update()
        cleaner = vtk.vtkCleanPolyData()
        cleaner.SetInputConnection(append_filter.GetOutputPort())
        cleaner.Update()
        
        self.combined_brain_mesh = cleaner.GetOutput()
        
        # Create brain actor
        brain_mapper = vtk.vtkPolyDataMapper()
        brain_mapper.SetInputData(self.combined_brain_mesh)
        
        brain_actor = vtk.vtkActor()
        brain_actor.SetMapper(brain_mapper)
        brain_actor.GetProperty().SetColor(0.85, 0.7, 0.65)
        brain_actor.GetProperty().SetOpacity(0.4)
        brain_actor.GetProperty().SetSpecular(0.3)
        brain_actor.GetProperty().SetSpecularPower(20)
        
        self.renderer.AddActor(brain_actor)
        
        # Get brain geometry
        bounds = self.combined_brain_mesh.GetBounds()
        self.brain_center = np.array(self.combined_brain_mesh.GetCenter())
        self.brain_scale = max(bounds[1]-bounds[0], bounds[3]-bounds[2], bounds[5]-bounds[4]) / 2
        
        print(f"✓ Brain center: ({self.brain_center[0]:.1f}, {self.brain_center[1]:.1f}, {self.brain_center[2]:.1f})")
        print(f"✓ Brain scale: {self.brain_scale:.1f}")
        
        # Build point locator
        self.point_locator = vtk.vtkPointLocator()
        self.point_locator.SetDataSet(self.combined_brain_mesh)
        self.point_locator.BuildLocator()
        
        # Build cell locator for surface projection
        self.cell_locator = vtk.vtkCellLocator()
        self.cell_locator.SetDataSet(self.combined_brain_mesh)
        self.cell_locator.BuildLocator()
        
        # Map electrodes
        self._map_electrodes_to_surface()
        
        # Create flow texture
        self._create_flow_texture()
        
        # Create surface-based signal paths
        self._create_surface_paths()
        
        # Setup lighting
        light1 = vtk.vtkLight()
        light1.SetPosition(self.brain_scale * 2, self.brain_scale * 2, self.brain_scale * 2)
        light1.SetIntensity(0.8)
        self.renderer.AddLight(light1)
        
        light2 = vtk.vtkLight()
        light2.SetPosition(-self.brain_scale * 2, -self.brain_scale * 2, self.brain_scale * 2)
        light2.SetIntensity(0.5)
        self.renderer.AddLight(light2)
        
        # Setup camera
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(self.brain_center[0], 
                          self.brain_center[1] - self.brain_scale * 3.5,
                          self.brain_center[2] + self.brain_scale * 0.5)
        camera.SetFocalPoint(self.brain_center[0], self.brain_center[1], self.brain_center[2])
        camera.SetViewUp(0, 0, 1)
        
        self.renderer.ResetCamera()
        self.vtkWidget.Initialize()
        
        print(f"✓ 3D visualization ready")

    def _map_electrodes_to_surface(self):
        """Map EEG electrodes to brain surface"""
        print(f"\n✓ Mapping {len(self.ch_names)} EEG electrodes:")
        
        self.electrode_mapping = {}
        
        for ch_idx, ch_name in enumerate(self.ch_names):
            # Clean the channel name - remove dots and uppercase
            clean_name = ch_name.strip().replace('.', '').upper()
            
            matched_pos = None
            matched_std_name = None
            
            # Direct exact match first
            if clean_name in ELECTRODE_POSITIONS_10_20:
                matched_pos = ELECTRODE_POSITIONS_10_20[clean_name]
                matched_std_name = clean_name
            
            if matched_pos:
                ideal_pos = spherical_to_cartesian(matched_pos[0], matched_pos[1], 
                                                   matched_pos[2], 
                                                   self.brain_center, self.brain_scale)
                
                closest_id = self.point_locator.FindClosestPoint(ideal_pos)
                surface_pos = np.array(self.combined_brain_mesh.GetPoint(closest_id))
                
                self.electrode_mapping[ch_name] = {
                    'index': ch_idx,
                    'std_name': matched_std_name,
                    'position': surface_pos
                }
                
                # Show position type
                y_pos = surface_pos[1] - self.brain_center[1]
                if y_pos > self.brain_scale * 0.3:
                    region = "FRONT"
                elif y_pos < -self.brain_scale * 0.3:
                    region = "BACK"
                else:
                    region = "MIDDLE"
                
                print(f"  {ch_name:8s} → {matched_std_name:5s} [{region}]")
            else:
                print(f"  {ch_name:8s} → NOT MATCHED (cleaned: {clean_name})")
        
        print(f"\n✓ Mapped {len(self.electrode_mapping)} / {len(self.ch_names)} electrodes")
        
        # Count by region
        front_count = sum(1 for e in self.electrode_mapping.values() 
                         if (e['position'][1] - self.brain_center[1]) > self.brain_scale * 0.3)
        back_count = sum(1 for e in self.electrode_mapping.values() 
                        if (e['position'][1] - self.brain_center[1]) < -self.brain_scale * 0.3)
        middle_count = len(self.electrode_mapping) - front_count - back_count
        
        print(f"  Frontal region: {front_count} electrodes")
        print(f"  Central region: {middle_count} electrodes")
        print(f"  Posterior region: {back_count} electrodes")

    def _project_to_surface(self, point):
        """Project a point onto brain surface"""
        closest_point = [0.0, 0.0, 0.0]
        cell_id = vtk.reference(0)
        sub_id = vtk.reference(0)
        dist2 = vtk.reference(0.0)
        
        self.cell_locator.FindClosestPoint(point, closest_point, cell_id, sub_id, dist2)
        return np.array(closest_point)

    def _create_surface_paths(self):
        """Create paths that lie on brain surface"""
        print(f"\n✓ Creating surface-based signal paths:")
        
        self.arc_paths = []
        
        # Comprehensive electrode pairs covering ENTIRE brain
        electrode_pairs = [
            # === FRONTAL REGION ===
            ('FP1', 'FP2'), ('F3', 'F4'), ('F5', 'F6'), ('F7', 'F8'),
            ('AF3', 'AF4'), ('AF7', 'AF8'),
            ('FP1', 'AF3'), ('FP2', 'AF4'),
            ('AF3', 'F3'), ('AF4', 'F4'),
            ('F3', 'F1'), ('F4', 'F2'),
            ('F1', 'FZ'), ('F2', 'FZ'),
            
            # === FRONTO-CENTRAL REGION ===
            ('FC5', 'FC6'), ('FC3', 'FC4'), ('FC1', 'FC2'),
            ('F3', 'FC3'), ('F4', 'FC4'),
            ('FC1', 'FCZ'), ('FC2', 'FCZ'),
            ('FZ', 'FCZ'), ('FCZ', 'CZ'),
            
            # === CENTRAL REGION ===
            ('C5', 'C6'), ('C3', 'C4'), ('C1', 'C2'),
            ('FC3', 'C3'), ('FC4', 'C4'),
            ('C1', 'CZ'), ('C2', 'CZ'),
            
            # === TEMPORAL REGION ===
            ('FT7', 'FT8'), ('T7', 'T8'),
            ('F7', 'FT7'), ('F8', 'FT8'),
            ('FT7', 'T7'), ('FT8', 'T8'),
            ('FC5', 'FT7'), ('FC6', 'FT8'),
            ('C5', 'T7'), ('C6', 'T8'),
            
            # === CENTRO-PARIETAL REGION ===
            ('CP5', 'CP6'), ('CP3', 'CP4'), ('CP1', 'CP2'),
            ('C3', 'CP3'), ('C4', 'CP4'),
            ('CP1', 'CPZ'), ('CP2', 'CPZ'),
            ('CZ', 'CPZ'), ('CPZ', 'PZ'),
            
            # === TEMPORO-PARIETAL REGION ===
            ('TP7', 'TP8'),
            ('T7', 'TP7'), ('T8', 'TP8'),
            ('CP5', 'TP7'), ('CP6', 'TP8'),
            ('TP7', 'P7'), ('TP8', 'P8'),
            
            # === PARIETAL REGION ===
            ('P7', 'P8'), ('P5', 'P6'), ('P3', 'P4'), ('P1', 'P2'),
            ('CP3', 'P3'), ('CP4', 'P4'),
            ('P1', 'PZ'), ('P2', 'PZ'),
            
            # === PARIETO-OCCIPITAL REGION ===
            ('PO7', 'PO8'), ('PO3', 'PO4'),
            ('P7', 'PO7'), ('P8', 'PO8'),
            ('P3', 'PO3'), ('P4', 'PO4'),
            ('PO3', 'POZ'), ('PO4', 'POZ'),
            ('PZ', 'POZ'), ('POZ', 'OZ'),
            
            # === OCCIPITAL REGION ===
            ('O1', 'O2'),
            ('PO3', 'O1'), ('PO4', 'O2'),
            ('O1', 'OZ'), ('O2', 'OZ'),
            
            # === LONG-RANGE CONNECTIONS ===
            ('FP1', 'CP1'), ('FP2', 'CP2'),
            ('AF3', 'P3'), ('AF4', 'P4'),
            ('F3', 'P3'), ('F4', 'P4'),
            ('FC3', 'PO3'), ('FC4', 'PO4'),
            ('F3', 'CP4'), ('F4', 'CP3'),
            ('F7', 'P7'), ('F8', 'P8'),
            ('FT7', 'TP7'), ('FT8', 'TP8'),
        ]
        
        for std1, std2 in electrode_pairs:
            ch1_name = None
            ch2_name = None
            
            for ch_name, info in self.electrode_mapping.items():
                if info['std_name'] == std1:
                    ch1_name = ch_name
                if info['std_name'] == std2:
                    ch2_name = ch_name
            
            if ch1_name and ch2_name:
                pos1 = self.electrode_mapping[ch1_name]['position']
                pos2 = self.electrode_mapping[ch2_name]['position']
                ch1_idx = self.electrode_mapping[ch1_name]['index']
                ch2_idx = self.electrode_mapping[ch2_name]['index']
                
                # Create path ON surface (not arced above)
                path_points = []
                num_points = 30
                
                for i in range(num_points):
                    t = i / (num_points - 1)
                    # Linear interpolation
                    interp_point = pos1 + t * (pos2 - pos1)
                    # Project to surface - THIS IS KEY!
                    surface_point = self._project_to_surface(interp_point)
                    path_points.append(surface_point)
                
                # Create smooth spline through surface points
                spline = vtk.vtkParametricSpline()
                points = vtk.vtkPoints()
                for p in path_points:
                    points.InsertNextPoint(p)
                spline.SetPoints(points)
                
                spline_source = vtk.vtkParametricFunctionSource()
                spline_source.SetParametricFunction(spline)
                spline_source.SetUResolution(150)
                spline_source.Update()
                
                # Create thin tube
                tube = vtk.vtkTubeFilter()
                tube.SetInputConnection(spline_source.GetOutputPort())
                tube.SetRadius(self.brain_scale * 0.008)
                tube.SetNumberOfSides(12)
                tube.SetGenerateTCoordsToNormalizedLength()
                tube.Update()
                
                # Create actor
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(tube.GetOutputPort())
                
                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.SetTexture(self.flow_texture)
                actor.GetProperty().SetOpacity(0.0)
                
                self.arc_paths.append({
                    'ch_indices': (ch1_idx, ch2_idx),
                    'ch_names': (ch1_name, ch2_name),
                    'std_names': (std1, std2),
                    'actor': actor
                })
                
                self.renderer.AddActor(actor)
                print(f"  Created path: {std1} ↔ {std2}")
            else:
                if not ch1_name and not ch2_name:
                    pass  # Both missing, skip silently
                elif not ch1_name:
                    print(f"  Skipped {std1} ↔ {std2}: {std1} not found")
                else:
                    print(f"  Skipped {std1} ↔ {std2}: {std2} not found")
        
        print(f"\n✓ Created {len(self.arc_paths)} surface paths")
        
        # Count paths by region
        frontal_paths = 0
        central_paths = 0
        posterior_paths = 0
        
        for path in self.arc_paths:
            ch1_name, ch2_name = path['ch_names']
            pos1 = self.electrode_mapping[ch1_name]['position']
            pos2 = self.electrode_mapping[ch2_name]['position']
            avg_y = ((pos1[1] + pos2[1]) / 2) - self.brain_center[1]
            
            if avg_y > self.brain_scale * 0.2:
                frontal_paths += 1
            elif avg_y < -self.brain_scale * 0.2:
                posterior_paths += 1
            else:
                central_paths += 1
        
        print(f"  Frontal paths: {frontal_paths}")
        print(f"  Central paths: {central_paths}")
        print(f"  Posterior paths: {posterior_paths}")

    def _create_flow_texture(self):
        """Create flowing gradient texture - BRIGHT colors"""
        self.flow_texture = vtk.vtkTexture()
        
        # Color transfer function - BRIGHTER hot colors
        c_transfer = vtk.vtkColorTransferFunction()
        c_transfer.AddRGBPoint(0.0, 0, 0, 0)
        c_transfer.AddRGBPoint(0.15, 1.0, 0, 0)
        c_transfer.AddRGBPoint(0.35, 1.0, 0.6, 0)
        c_transfer.AddRGBPoint(0.5, 1.0, 1.0, 0.8)
        c_transfer.AddRGBPoint(0.65, 1.0, 0.6, 0)
        c_transfer.AddRGBPoint(0.85, 1.0, 0, 0)
        c_transfer.AddRGBPoint(1.0, 0, 0, 0)
        
        # Alpha transfer function
        a_transfer = vtk.vtkPiecewiseFunction()
        a_transfer.AddPoint(0.0, 0.0)
        a_transfer.AddPoint(0.15, 0.9)
        a_transfer.AddPoint(0.5, 1.0)
        a_transfer.AddPoint(0.85, 0.9)
        a_transfer.AddPoint(1.0, 0.0)
        
        # Create texture image
        texture_res = 512
        image_data = vtk.vtkImageData()
        image_data.SetDimensions(texture_res, 1, 1)
        
        scalars = vtk.vtkUnsignedCharArray()
        scalars.SetNumberOfComponents(4)
        scalars.SetNumberOfTuples(texture_res)
        
        for i in range(texture_res):
            t = i / (texture_res - 1.0)
            rgb = c_transfer.GetColor(t)
            alpha = a_transfer.GetValue(t)
            scalars.SetTuple4(i, 
                            int(rgb[0]*255), 
                            int(rgb[1]*255), 
                            int(rgb[2]*255), 
                            int(alpha*255))
        
        image_data.GetPointData().SetScalars(scalars)
        self.flow_texture.SetInputData(image_data)
        self.flow_texture.RepeatOn()
        self.flow_texture.SetInterpolate(1)

    def _animation_loop(self):
        """Main animation loop"""
        if not self.is_playing:
            return
        
        current_time = self.current_frame / self.sfreq
        
        # Get current EEG amplitudes
        current_amps = self.data_normalized[:, self.current_frame] * self.intensity
        
        # Reset all paths
        for arc in self.arc_paths:
            arc['actor'].GetProperty().SetOpacity(0.0)
        
        active_paths = 0
        
        for i, arc in enumerate(self.arc_paths):
            ch1_idx, ch2_idx = arc['ch_indices']
            ch1_amp = current_amps[ch1_idx]
            ch2_amp = current_amps[ch2_idx]
            activity = (ch1_amp + ch2_amp) / 2
            
            # Get path region to adjust threshold
            ch1_name, ch2_name = arc['ch_names']
            pos1 = self.electrode_mapping[ch1_name]['position']
            pos2 = self.electrode_mapping[ch2_name]['position']
            avg_y = ((pos1[1] + pos2[1]) / 2) - self.brain_center[1]
            
            # Different thresholds for different regions - ADJUSTED
            if avg_y > self.brain_scale * 0.2:  # Frontal
                threshold = 0.15
            elif avg_y < -self.brain_scale * 0.2:  # Posterior
                threshold = 0.35
            else:  # Central
                threshold = 0.25
            
            if activity > threshold:
                arc['actor'].GetProperty().SetOpacity(1.0)
                active_paths += 1
                
                # Animate texture continuously
                texture_transform = arc['actor'].GetTexture().GetTransform()
                if texture_transform is None:
                    texture_transform = vtk.vtkTransform()
                    arc['actor'].GetTexture().SetTransform(texture_transform)
                
                texture_transform.Identity()
                texture_transform.Translate(-(current_time % 1.0) * 1.0, 0, 0)
        
        # Advance frame
        frame_skip = max(1, int(self.sfreq / (30 * self.speed)))
        self.current_frame = (self.current_frame + frame_skip) % self.n_samples
        
        # Update info
        avg_activity = np.mean(current_amps)
        time_sec = (self.current_frame / self.sfreq) % (self.n_samples / self.sfreq)
        
        info_text = (f"Dataset: S002R01 (Resting)\n"
                    f"Time: {time_sec:.1f}s / {self.n_samples/self.sfreq:.1f}s\n"
                    f"Activity: {avg_activity*100:.0f}%\n"
                    f"Active Flows: {active_paths}/{len(self.arc_paths)}\n"
                    f"Speed: {self.speed:.1f}x")
        self.info_text.setText(info_text)
        
        self.vtkWidget.GetRenderWindow().Render()

    def _toggle_play_pause(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_pause_btn.setText("⏸️ Pause")
        else:
            self.play_pause_btn.setText("▶️ Play")

    def _reset_animation(self):
        self.current_frame = 0


if __name__ == "__main__":
    if not (MNE_AVAILABLE and SCIPY_AVAILABLE):
        print("\n" + "="*70)
        print("ERROR: Missing libraries")
        print("Install: pip install mne scipy PyQt5 vtk")
        print("="*70)
        sys.exit(1)
    
    MODEL_FOLDER = r"D:\task3\Moving Stuff\BP3D_brain"
    EDF_PATH = r"D:\task3\Moving Stuff\S002R01.edf"
    
    if not os.path.exists(MODEL_FOLDER) or not os.path.exists(EDF_PATH):
        print(f"\n✗ ERROR: Check paths")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("⚡ BRAIN EEG SURFACE-BASED VISUALIZATION")
    print("="*70)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = BrainEEGVisualizerApp(MODEL_FOLDER, EDF_PATH)
    window.show()
    
    print("\n✓ Application ready - signals across entire brain with organized flow!")
    print("="*70 + "\n")
    
    sys.exit(app.exec_())