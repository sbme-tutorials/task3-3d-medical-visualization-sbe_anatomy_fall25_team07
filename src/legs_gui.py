import sys
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QGroupBox, QLabel, 
                             QSlider, QFileDialog, QListWidget, QListWidgetItem,
                             QCheckBox, QScrollArea, QStatusBar, QFrame)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk


class LegVisualizationGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Medical Leg Anatomy Visualization System")
        
        # Get screen size and set window size
        screen = QApplication.primaryScreen().geometry()
        width = int(screen.width() * 0.85)
        height = int(screen.height() * 0.85)
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)
        
        # Apply modern stylesheet
        self.setStyleSheet(self.get_stylesheet())
        
        # Initialize data variables
        self.leg_parts = {}
        self.color_index = 0
        self.clip_planes = {'x': None, 'y': None}
        
        # Realistic leg anatomy colors
        self.colors = [
            # Bone colors
            (0.95, 0.92, 0.88),  # Bone ivory/cream
            (0.93, 0.90, 0.85),  # Light bone
            (0.90, 0.87, 0.82),  # Natural bone
            (0.88, 0.85, 0.80),  # Darker bone
            
            # Muscle colors
            (0.72, 0.26, 0.26),  # Deep muscle red
            (0.78, 0.32, 0.32),  # Muscle tissue
            (0.65, 0.20, 0.20),  # Dark muscle
            (0.82, 0.38, 0.38),  # Light muscle
            (0.75, 0.28, 0.28),  # Standard muscle
            
            # Connective tissue & tendons
            (0.92, 0.88, 0.82),  # Tendon beige
            (0.95, 0.91, 0.85),  # Light tendon
            (0.88, 0.84, 0.78),  # Connective tissue
            
            # Fat tissue
            (0.96, 0.90, 0.70),  # Subcutaneous fat (yellowish)
            (0.98, 0.93, 0.75),  # Light fat
            
            # Cartilage
            (0.85, 0.90, 0.92),  # Cartilage (bluish white)
            (0.82, 0.88, 0.90),  # Darker cartilage
        ]
        
        # Setup UI
        self.setup_ui()
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.setStyleSheet("background-color: #1a1d23; color: #8892b0; padding: 5px;")
        self.show_message("🚀 System Ready - Load leg anatomy data to begin visualization")
    
    def get_stylesheet(self):
        """Modern dark theme stylesheet"""
        return """
            QMainWindow {
                background-color: #0d1117;
            }
            
            QWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
            }
            
            QGroupBox {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 18px;
                font-weight: bold;
                color: #79c0ff;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 10px;
                color: #79c0ff;
                font-size: 12px;
                font-weight: bold;
            }
            
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 11px;
                font-weight: 600;
                text-align: left;
            }
            
            QPushButton:hover {
                background-color: #30363d;
                border: 1px solid #79c0ff;
                color: #79c0ff;
            }
            
            QPushButton:pressed {
                background-color: #0d1117;
                border: 1px solid #79c0ff;
            }
            
            QPushButton#primaryButton {
                background-color: #1f6feb;
                color: white;
                border: 1px solid #388bfd;
            }
            
            QPushButton#primaryButton:hover {
                background-color: #388bfd;
                border: 1px solid #58a6ff;
            }
            
            QPushButton#secondaryButton {
                background-color: #238636;
                color: white;
                border: 1px solid #2ea043;
            }
            
            QPushButton#secondaryButton:hover {
                background-color: #2ea043;
                border: 1px solid #3fb950;
            }
            
            QPushButton#dangerButton {
                background-color: #da3633;
                color: white;
                border: 1px solid #f85149;
            }
            
            QPushButton#dangerButton:hover {
                background-color: #f85149;
            }
            
            QLabel {
                color: #c9d1d9;
                background: transparent;
                border: none;
            }
            
            QLabel#titleLabel {
                font-size: 20px;
                font-weight: bold;
                color: #79c0ff;
                padding: 8px;
            }
            
            QLabel#subtitleLabel {
                font-size: 11px;
                color: #8b949e;
            }
            
            QLabel#sectionLabel {
                font-size: 11px;
                font-weight: 600;
                color: #8b949e;
                padding: 4px 0px;
            }
            
            QSlider::groove:horizontal {
                background: #21262d;
                height: 6px;
                border-radius: 3px;
                border: 1px solid #30363d;
            }
            
            QSlider::handle:horizontal {
                background: #79c0ff;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
                border: 2px solid #0d1117;
            }
            
            QSlider::handle:horizontal:hover {
                background: #a5d6ff;
                border: 2px solid #79c0ff;
            }
            
            QSlider::sub-page:horizontal {
                background: #1f6feb;
                border-radius: 3px;
            }
            
            QListWidget {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }
            
            QListWidget::item {
                background-color: #161b22;
                color: #c9d1d9;
                border: 1px solid #21262d;
                border-radius: 4px;
                padding: 8px;
                margin: 2px;
            }
            
            QListWidget::item:hover {
                background-color: #21262d;
                border: 1px solid #79c0ff;
            }
            
            QListWidget::item:selected {
                background-color: #1f6feb;
                color: white;
                border: 1px solid #79c0ff;
            }
            
            QScrollArea {
                background-color: #0d1117;
                border: none;
            }
            
            QScrollBar:vertical {
                background: #161b22;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #30363d;
                border-radius: 6px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #484f58;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QFrame#separatorLine {
                background-color: #30363d;
                max-height: 1px;
            }
            
            QCheckBox {
                color: #c9d1d9;
                spacing: 5px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #30363d;
                background-color: #21262d;
            }
            
            QCheckBox::indicator:hover {
                border: 1px solid #79c0ff;
                background-color: #30363d;
            }
            
            QCheckBox::indicator:checked {
                background-color: #1f6feb;
                border: 1px solid #388bfd;
                image: url(none);
            }
            
            QCheckBox::indicator:checked:hover {
                background-color: #388bfd;
            }
        """
    
    def setup_ui(self):
        """Setup the main user interface"""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_widget.setLayout(main_layout)
        
        # Left panel container
        left_container = QFrame()
        left_container.setStyleSheet("background-color: #0d1117; border-right: 1px solid #30363d;")
        left_container.setMaximumWidth(360)
        left_container.setMinimumWidth(360)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # Header Section
        header = QFrame()
        header.setStyleSheet("background-color: #161b22; border-bottom: 1px solid #30363d;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        title = QLabel("🦵 Leg Anatomy Visualization")
        title.setObjectName("titleLabel")
        header_layout.addWidget(title)
        
        subtitle = QLabel("3D Musculoskeletal Imaging System v2.0")
        subtitle.setObjectName("subtitleLabel")
        header_layout.addWidget(subtitle)
        
        left_layout.addWidget(header)
        
        # Scrollable control panel
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none;")
        
        self.control_panel_widget = QWidget()
        control_layout = QVBoxLayout()
        control_layout.setContentsMargins(15, 15, 15, 15)
        control_layout.setSpacing(15)
        self.control_panel_widget.setLayout(control_layout)
        
        # === DATA LOADING ===
        data_group = QGroupBox("📁 Data Loading")
        data_layout = QVBoxLayout()
        data_layout.setSpacing(8)
        
        self.load_single_btn = QPushButton("📄 Load Single OBJ File")
        self.load_single_btn.setObjectName("primaryButton")
        self.load_single_btn.clicked.connect(self.load_single_obj)
        data_layout.addWidget(self.load_single_btn)
        
        self.load_folder_btn = QPushButton("📁 Load Folder (Batch Import)")
        self.load_folder_btn.setObjectName("secondaryButton")
        self.load_folder_btn.clicked.connect(self.load_folder_obj)
        data_layout.addWidget(self.load_folder_btn)
        
        separator = QFrame()
        separator.setObjectName("separatorLine")
        data_layout.addWidget(separator)
        
        self.data_label = QLabel("No data loaded")
        self.data_label.setObjectName("subtitleLabel")
        self.data_label.setAlignment(Qt.AlignCenter)
        data_layout.addWidget(self.data_label)
        
        data_group.setLayout(data_layout)
        control_layout.addWidget(data_group)
        
        # === LOADED LEG PARTS ===
        parts_group = QGroupBox("🦴 Loaded Anatomy Components")
        parts_layout = QVBoxLayout()
        parts_layout.setSpacing(8)
        
        list_label = QLabel("Toggle visibility:")
        list_label.setObjectName("sectionLabel")
        parts_layout.addWidget(list_label)
        
        self.parts_list = QListWidget()
        self.parts_list.setMaximumHeight(180)
        self.parts_list.itemChanged.connect(self.toggle_part_visibility)
        parts_layout.addWidget(self.parts_list)
        
        parts_buttons_layout = QHBoxLayout()
        parts_buttons_layout.setSpacing(8)
        
        self.show_all_btn = QPushButton("👁️ Show All")
        self.show_all_btn.clicked.connect(self.show_all_parts)
        parts_buttons_layout.addWidget(self.show_all_btn)
        
        self.hide_all_btn = QPushButton("🙈 Hide All")
        self.hide_all_btn.clicked.connect(self.hide_all_parts)
        parts_buttons_layout.addWidget(self.hide_all_btn)
        
        parts_layout.addLayout(parts_buttons_layout)
        parts_group.setLayout(parts_layout)
        control_layout.addWidget(parts_group)
        
        # === VISUALIZATION METHODS ===
        viz_group = QGroupBox("🎨 Visualization Modes")
        viz_layout = QVBoxLayout()
        viz_layout.setSpacing(8)
        
        self.surface_btn = QPushButton("🦴 Surface Rendering")
        self.surface_btn.clicked.connect(self.surface_rendering)
        viz_layout.addWidget(self.surface_btn)
        
        self.clipping_btn = QPushButton("✂️ Clipping Planes")
        self.clipping_btn.clicked.connect(self.clipping_planes)
        viz_layout.addWidget(self.clipping_btn)
        
        
        viz_group.setLayout(viz_layout)
        control_layout.addWidget(viz_group)
        
        # === NAVIGATION TECHNIQUES ===
        nav_group = QGroupBox("🧭 Navigation Tools")
        nav_layout = QVBoxLayout()
        nav_layout.setSpacing(8)
        
        self.focus_nav_btn = QPushButton("🔍 Focus Navigation")
        self.focus_nav_btn.clicked.connect(self.focus_navigation)
        self.focus_nav_btn.setEnabled(True)
        nav_layout.addWidget(self.focus_nav_btn)
        
        
        
        self.flythrough_btn = QPushButton("✈️ Fly-through Mode")
        self.flythrough_btn.clicked.connect(self.flythrough_navigation)
        self.flythrough_btn.setEnabled(True)
        nav_layout.addWidget(self.flythrough_btn)
        
        nav_group.setLayout(nav_layout)
        control_layout.addWidget(nav_group)
        
        # === GLOBAL CONTROLS ===
        controls_group = QGroupBox("⚙️ Global Controls")
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(10)
        
        # Opacity slider
        opacity_label = QLabel("Transparency Level:")
        opacity_label.setObjectName("sectionLabel")
        controls_layout.addWidget(opacity_label)
        
        opacity_container = QHBoxLayout()
        opacity_container.setSpacing(10)
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        opacity_container.addWidget(self.opacity_slider)
        
        self.opacity_value_label = QLabel("100%")
        self.opacity_value_label.setObjectName("sectionLabel")
        self.opacity_value_label.setMinimumWidth(45)
        self.opacity_value_label.setAlignment(Qt.AlignCenter)
        self.opacity_value_label.setStyleSheet("background: #21262d; border: 1px solid #30363d; border-radius: 4px; padding: 4px;")
        opacity_container.addWidget(self.opacity_value_label)
        
        controls_layout.addLayout(opacity_container)
        
        separator2 = QFrame()
        separator2.setObjectName("separatorLine")
        controls_layout.addWidget(separator2)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        self.reset_btn = QPushButton("🔄 Reset")
        self.reset_btn.clicked.connect(self.reset_view)
        buttons_layout.addWidget(self.reset_btn)
        
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.setObjectName("dangerButton")
        self.clear_btn.clicked.connect(self.clear_all)
        buttons_layout.addWidget(self.clear_btn)
        
        controls_layout.addLayout(buttons_layout)
        controls_group.setLayout(controls_layout)
        control_layout.addWidget(controls_group)
        
        # Add stretch
        control_layout.addStretch()
        
        scroll.setWidget(self.control_panel_widget)
        left_layout.addWidget(scroll)
        
        # === VTK RENDERING WINDOW ===
        right_container = QFrame()
        right_container.setStyleSheet("background-color: #0d1117;")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # VTK info bar
        vtk_header = QFrame()
        vtk_header.setStyleSheet("background-color: #161b22; border-bottom: 1px solid #30363d;")
        vtk_header_layout = QHBoxLayout(vtk_header)
        vtk_header_layout.setContentsMargins(20, 10, 20, 10)
        
        self.info_label = QLabel("🎯 Viewport: Ready for rendering")
        self.info_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        vtk_header_layout.addWidget(self.info_label)
        vtk_header_layout.addStretch()
        
        render_info = QLabel("Interactive 3D View | Use mouse to rotate")
        render_info.setStyleSheet("color: #6e7681; font-size: 10px;")
        vtk_header_layout.addWidget(render_info)
        
        right_layout.addWidget(vtk_header)
        
        # VTK Widget
        self.vtk_widget = QVTKRenderWindowInteractor(right_container)
        
        # VTK Renderer
        self.renderer = vtk.vtkRenderer()
        
        # Medical imaging background
        self.renderer.GradientBackgroundOn()
        self.renderer.SetBackground(0.02, 0.02, 0.05)
        self.renderer.SetBackground2(0.06, 0.08, 0.10)
        
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        
        right_layout.addWidget(self.vtk_widget)
        
        # Add to main layout
        main_layout.addWidget(left_container)
        main_layout.addWidget(right_container)
        
        # Initialize
        self.interactor.Initialize()
        self.interactor.Start()
    
    # ========== DATA LOADING FUNCTIONS ==========
    
    def load_single_obj(self):
        """Load a single OBJ file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Load Leg Anatomy Model", 
            "", 
            "3D Models (*.obj *.stl *.ply);;OBJ Files (*.obj);;All Files (*.*)"
        )
        if file_path:
            self.load_obj_file(file_path)
    
    def load_folder_obj(self):
        """Load all OBJ files from a folder"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with Leg Anatomy Models"
        )
        if not folder_path:
            return
            
        try:
            all_files = os.listdir(folder_path)
            self.show_message(f"📂 Scanning folder: {len(all_files)} files found")
            
            obj_files = [f for f in all_files if f.lower().endswith('.obj')]
            
            if not obj_files:
                self.show_message(f"⚠️ No OBJ files found in selected folder")
                return
            
            self.show_message(f"🔄 Loading {len(obj_files)} anatomy components...")
            
            loaded_count = 0
            for i, obj_file in enumerate(obj_files):
                filepath = os.path.join(folder_path, obj_file)
                
                if (i + 1) % 10 == 0:
                    self.show_message(f"⏳ Progress: {i+1}/{len(obj_files)} files")
                
                try:
                    self.load_obj_file(filepath)
                    loaded_count += 1
                except Exception as e:
                    print(f"Failed: {obj_file}: {str(e)}")
            
            self.data_label.setText(f"✅ {loaded_count} components loaded")
            self.data_label.setStyleSheet("color: #3fb950; font-weight: bold;")
            self.show_message(f"✅ Successfully loaded {loaded_count} anatomy parts")
            
            if loaded_count > 0:
                self.renderer.ResetCamera()
                self.vtk_widget.GetRenderWindow().Render()
                self.info_label.setText(f"🎯 Viewport: Rendering {loaded_count} components")
                
        except Exception as e:
            self.show_message(f"❌ Error: {str(e)}")
    
    def load_obj_file(self, file_path):
        """Load a single OBJ file with smart coloring"""
        try:
            filename = os.path.basename(file_path)
            
            if filename in self.leg_parts:
                self.show_message(f"⚠️ {filename} already loaded")
                return
            
            reader = vtk.vtkOBJReader()
            reader.SetFileName(file_path)
            reader.Update()
            
            polydata = reader.GetOutput()
            
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)
            
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            
            # 🎨 تلوين ذكي حسب نوع الجزء
            color = self.get_smart_color(filename)
            actor.GetProperty().SetColor(color)
            actor.GetProperty().SetSpecular(0.4)
            actor.GetProperty().SetSpecularPower(20)
            actor.GetProperty().SetAmbient(0.3)
            actor.GetProperty().SetDiffuse(0.7)
            actor.GetProperty().SetInterpolationToPhong()
            
            self.leg_parts[filename] = {
                "actor": actor,
                "mapper": mapper,
                "data": polydata,
                "color": color
            }
            
            self.renderer.AddActor(actor)
            
            item = QListWidgetItem(f"● {filename}")
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, filename)
            self.parts_list.addItem(item)
            
            self.show_message(f"✅ Loaded: {filename}")
            
        except Exception as e:
            self.show_message(f"❌ Failed to load {filename}: {str(e)}")
    
    def toggle_part_visibility(self, item):
        """Toggle visibility"""
        filename = item.data(Qt.UserRole)
        if filename and filename in self.leg_parts:
            is_checked = item.checkState() == Qt.Checked
            actor = self.leg_parts[filename]["actor"]
            actor.SetVisibility(is_checked)
            self.vtk_widget.GetRenderWindow().Render()
    
    def show_all_parts(self):
        """Show all parts"""
        for i in range(self.parts_list.count()):
            self.parts_list.item(i).setCheckState(Qt.Checked)
        self.show_message("✅ All components visible")
    
    def hide_all_parts(self):
        """Hide all parts"""
        for i in range(self.parts_list.count()):
            self.parts_list.item(i).setCheckState(Qt.Unchecked)
        self.show_message("🙈 All components hidden")
    
    # ========== VISUALIZATION METHODS ==========
    
    def surface_rendering(self):
        """Surface Rendering"""
        if not self.leg_parts:
            self.show_message("⚠️ Please load leg anatomy data first")
            return
        
        for part_data in self.leg_parts.values():
            part_data["actor"].SetVisibility(True)
            part_data["actor"].GetProperty().SetOpacity(0.95)
        
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()
        self.show_message(f"🦴 Surface Rendering: {len(self.leg_parts)} components displayed")
        self.info_label.setText(f"🎯 Mode: Surface Rendering | Components: {len(self.leg_parts)}")

    def get_smart_color(self, filename):
        """
        اختيار لون ذكي حسب نوع الجزء من اسم الملف
        """
        filename_lower = filename.lower()
        
        # 🦴 BONE - عظام (ألوان فاتحة كريمية)
        bone_keywords = ['bone', 'femur', 'tibia', 'fibula', 'patella', 'tarsal', 
                        'metatarsal', 'phalang', 'skeleton', 'osseous']
        if any(keyword in filename_lower for keyword in bone_keywords):
            bone_colors = [
                (0.95, 0.92, 0.88),  # عاج فاتح
                (0.93, 0.90, 0.85),  # بيج عظمي
                (0.90, 0.87, 0.82),  # كريمي
                (0.88, 0.85, 0.80),  # بيج داكن
            ]
            return bone_colors[self.color_index % len(bone_colors)]
        
        # 💪 MUSCLE - عضلات (ألوان حمراء)
        muscle_keywords = ['muscle', 'gastrocnemius', 'soleus', 'quadriceps', 
                        'hamstring', 'biceps', 'triceps', 'vastus', 'rectus',
                        'sartorius', 'gracilis', 'adductor', 'gluteus']
        if any(keyword in filename_lower for keyword in muscle_keywords):
            muscle_colors = [
                (0.75, 0.28, 0.28),  # أحمر عضلي قوي
                (0.82, 0.35, 0.35),  # أحمر فاتح
                (0.68, 0.22, 0.22),  # أحمر داكن
                (0.78, 0.32, 0.32),  # أحمر متوسط
                (0.72, 0.26, 0.26),  # أحمر عميق
            ]
            return muscle_colors[self.color_index % len(muscle_colors)]
        
        # 🎗️ TENDON/LIGAMENT - أوتار/أربطة (بيج فاتح)
        tendon_keywords = ['tendon', 'ligament', 'achilles', 'patellar', 
                        'cruciate', 'collateral', 'meniscus']
        if any(keyword in filename_lower for keyword in tendon_keywords):
            tendon_colors = [
                (0.92, 0.88, 0.82),  # بيج أوتار
                (0.95, 0.91, 0.85),  # بيج فاتح
                (0.88, 0.84, 0.78),  # بيج متوسط
            ]
            return tendon_colors[self.color_index % len(tendon_colors)]
        
        # 🧈 FAT - دهون (أصفر باهت)
        fat_keywords = ['fat', 'adipose', 'subcutaneous']
        if any(keyword in filename_lower for keyword in fat_keywords):
            return (0.96, 0.90, 0.70)  # أصفر دهني
        
        # 🔵 CARTILAGE - غضاريف (أزرق فاتح)
        cartilage_keywords = ['cartilage', 'meniscus', 'articular']
        if any(keyword in filename_lower for keyword in cartilage_keywords):
            return (0.85, 0.90, 0.92)  # أزرق غضروفي
        
        # 🔴 BLOOD VESSELS - أوعية دموية (أحمر غامق)
        vessel_keywords = ['artery', 'vein', 'vessel', 'vascular']
        if any(keyword in filename_lower for keyword in vessel_keywords):
            return (0.65, 0.15, 0.15)  # أحمر دموي
        
        # 🟡 NERVES - أعصاب (أصفر شاحب)
        nerve_keywords = ['nerve', 'neural', 'sciatic', 'tibial', 'peroneal']
        if any(keyword in filename_lower for keyword in nerve_keywords):
            return (0.95, 0.92, 0.70)  # أصفر عصبي
        
        # 🌫️ SKIN - جلد (وردي فاتح)
        skin_keywords = ['skin', 'dermis', 'epidermis', 'cutaneous']
        if any(keyword in filename_lower for keyword in skin_keywords):
            return (0.95, 0.85, 0.80)  # وردي جلدي
        
        # ❓ DEFAULT - لو مش عارف النوع (رمادي أزرق)
        default_colors = [
            (0.60, 0.65, 0.70),
            (0.55, 0.60, 0.65),
            (0.65, 0.70, 0.75),
        ]
        return default_colors[self.color_index % len(default_colors)]

    def clipping_planes(self):
        """Enable clipping planes"""
        if not self.leg_parts:
            self.show_message("⚠️ Load leg anatomy data first")
            return
        
        if not hasattr(self, 'clipping_enabled'):
            self.clipping_enabled = True
            self.create_clipping_controls()
            self.show_message("✂️ Clipping mode activated - Use sliders to explore")
            self.info_label.setText("🎯 Mode: Clipping Planes | Slice through leg structure")
        else:
            self.show_message("⚠️ Clipping already enabled")
        
        self.vtk_widget.GetRenderWindow().Render()
    
    
    
    """
Focus Navigation Function for Visualization
Add this code to your VisualizationGUI class
"""

    def focus_navigation(self):
        """Enable focus mode - select a part to zoom and highlight"""
        if not self.leg_parts:
            self.show_message("⚠️ Load leg anatomy data first")
            return
        
        # Create focus selection dialog
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("🔍 Focus on leg  Component")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #161b22;
                color: #c9d1d9;
            }
            QLabel {
                color: #c9d1d9;
                font-size: 12px;
                padding: 5px;
            }
            QComboBox {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
            }
            QComboBox:hover {
                border: 1px solid #a991f7;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #c9d1d9;
                margin-right: 10px;
            }
            QPushButton {
                background-color: #6e40c9;
                color: white;
                border: 1px solid #8957e5;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #8957e5;
            }
            QPushButton#cancelBtn {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
            }
            QPushButton#cancelBtn:hover {
                background-color: #30363d;
                border: 1px solid #a991f7;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Select a leg component to focus on:")
        title.setStyleSheet("font-size: 13px; font-weight: bold; color: #a991f7;")
        layout.addWidget(title)
        
        # Dropdown with all parts
        combo = QComboBox()
        combo.addItem("-- Select Component --", None)
        for filename in sorted(self.leg_parts.keys()):
            combo.addItem(f"🧠 {filename}", filename)
        layout.addWidget(combo)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        focus_btn = QPushButton("🔍 Focus")
        focus_btn.clicked.connect(lambda: self.apply_focus(combo.currentData(), dialog))
        btn_layout.addWidget(focus_btn)
        
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec_()


    def apply_focus(self, selected_part, dialog):
        """Apply focus effect to selected part"""
        if not selected_part or selected_part not in self.leg_parts:
            self.show_message("⚠️ Please select a valid component")
            return
        
        dialog.accept()
        
        # Store focus state
        self.focused_part = selected_part
        
        # Get the bounds of the focused part
        focused_data = self.leg_parts[selected_part]["data"]
        bounds = focused_data.GetBounds()
        
        # Calculate center of the focused part
        center = [
            (bounds[0] + bounds[1]) / 2,
            (bounds[2] + bounds[3]) / 2,
            (bounds[4] + bounds[5]) / 2
        ]
        
        # Fade all other parts
        for filename, part_data in self.leg_parts.items():
            actor = part_data["actor"]
            if filename == selected_part:
                # Keep focused part at full opacity and brightness
                actor.GetProperty().SetOpacity(1.0)
                actor.GetProperty().SetAmbient(0.4)
                actor.GetProperty().SetDiffuse(0.8)
            else:
                # Fade other parts
                actor.GetProperty().SetOpacity(0.25)
                actor.GetProperty().SetAmbient(0.1)
                actor.GetProperty().SetDiffuse(0.4)
        
        # Smoothly zoom camera to focused part
        camera = self.renderer.GetActiveCamera()
        
        # Calculate zoom distance based on part size
        max_dimension = max(
            bounds[1] - bounds[0],
            bounds[3] - bounds[2],
            bounds[5] - bounds[4]
        )
        distance = max_dimension * 2.0
        
        # Get current camera position and calculate direction
        current_pos = camera.GetPosition()
        current_focal = camera.GetFocalPoint()
        
        # Calculate direction vector from current position to center
        direction = [
            center[0] - current_focal[0],
            center[1] - current_focal[1],
            center[2] - current_focal[2]
        ]
        
        # Normalize direction
        length = (direction[0]**2 + direction[1]**2 + direction[2]**2) ** 0.5
        if length > 0:
            direction = [d / length for d in direction]
        
        # Set new camera position
        new_pos = [
            center[0] - direction[0] * distance,
            center[1] - direction[1] * distance,
            center[2] - direction[2] * distance
        ]
        
        # Animate camera movement
        from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QVariantAnimation
        
        # Create animation for smooth transition
        self.camera_animation = QVariantAnimation(self)
        self.camera_animation.setDuration(800)  # 800ms animation
        self.camera_animation.setStartValue(0.0)
        self.camera_animation.setEndValue(1.0)
        self.camera_animation.setEasingCurve(QEasingCurve.InOutCubic)
        
        # Store start and end positions
        self.anim_start_pos = current_pos
        self.anim_end_pos = new_pos
        self.anim_start_focal = current_focal
        self.anim_end_focal = center
        
        def update_camera(value):
            # Interpolate position
            new_camera_pos = [
                self.anim_start_pos[0] + (self.anim_end_pos[0] - self.anim_start_pos[0]) * value,
                self.anim_start_pos[1] + (self.anim_end_pos[1] - self.anim_start_pos[1]) * value,
                self.anim_start_pos[2] + (self.anim_end_pos[2] - self.anim_start_pos[2]) * value
            ]
            
            new_focal_pos = [
                self.anim_start_focal[0] + (self.anim_end_focal[0] - self.anim_start_focal[0]) * value,
                self.anim_start_focal[1] + (self.anim_end_focal[1] - self.anim_start_focal[1]) * value,
                self.anim_start_focal[2] + (self.anim_end_focal[2] - self.anim_start_focal[2]) * value
            ]
            
            camera.SetPosition(new_camera_pos)
            camera.SetFocalPoint(new_focal_pos)
            self.vtk_widget.GetRenderWindow().Render()
        
        self.camera_animation.valueChanged.connect(update_camera)
        self.camera_animation.start()
        
        self.show_message(f"🔍 Focused on: {selected_part}")
        self.info_label.setText(f"🎯 Mode: Focus | Component: {selected_part}")
        
        # Enable unfocus button
        if not hasattr(self, 'unfocus_btn'):
            self.create_unfocus_button()
        else:
            self.unfocus_btn.setEnabled(True)


    def create_unfocus_button(self):
        """Create unfocus button in the navigation group"""
        # Find the navigation group and add unfocus button
        # This should be called after the UI is set up
        nav_group = None
        for i in range(self.control_panel_widget.layout().count()):
            item = self.control_panel_widget.layout().itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QGroupBox) and "Navigation" in widget.title():
                    nav_group = widget
                    break
        
        if nav_group:
            nav_layout = nav_group.layout()
            
            self.unfocus_btn = QPushButton("🔄 Reset Focus")
            self.unfocus_btn.clicked.connect(self.reset_focus)
            self.unfocus_btn.setEnabled(False)
            nav_layout.addWidget(self.unfocus_btn)


    def reset_focus(self):
        """Reset focus - restore all parts to normal opacity"""
        if not hasattr(self, 'focused_part'):
            return
        
        # Restore all parts to normal
        for part_data in self.leg_parts.values():
            actor = part_data["actor"]
            actor.GetProperty().SetOpacity(0.95)
            actor.GetProperty().SetAmbient(0.3)
            actor.GetProperty().SetDiffuse(0.7)
        
        # Reset camera to show all
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()
        
        # Clear focus state
        delattr(self, 'focused_part')
        
        self.show_message("🔄 Focus reset - All components visible")
        self.info_label.setText(f"🎯 Viewport: Rendering {len(self.leg_parts)} components")
        
        if hasattr(self, 'unfocus_btn'):
            self.unfocus_btn.setEnabled(False)


    # Don't forget to also modify the setup_ui method to enable the focus button:
    # Change this line:
    #   self.focus_nav_btn.setEnabled(False)
    # To:
    #   self.focus_nav_btn.setEnabled(True)  # Enable focus navigation
    
    
    def flythrough_navigation(self):
        
        """Launch the flythrough navigation window with data"""
        if not self.leg_parts:  # أو heart_parts أو leg_parts أو dental_parts
            self.show_message("⚠️ Please load data first")
            return
        
        try:
            from flyThrough2 import FlythroughWindow
            
            self.flythrough_window = FlythroughWindow(
                system_type="leg",  # أو "heart" أو "leg" أو "dental"
                parts_data=self.leg_parts  # 🔥 بعت الداتا مباشرة
            )
            self.flythrough_window.show()
            
            self.show_message(f"✈️ Flythrough opened with {len(self.brain_parts)} components")
            
        except Exception as e:
            self.show_message(f"❌ Error: {str(e)}")
    # ========== CONTROLS ==========
    
    def change_opacity(self, value):
        """Change opacity"""
        self.opacity_value_label.setText(f"{value}%")
        opacity = value / 100.0
        
        for part_data in self.leg_parts.values():
            part_data["actor"].GetProperty().SetOpacity(opacity)
        
        self.vtk_widget.GetRenderWindow().Render()
    
    def reset_view(self):
        """Reset view"""
        self.renderer.ResetCamera()
        self.opacity_slider.setValue(100)
        self.vtk_widget.GetRenderWindow().Render()
        self.show_message("🔄 View reset to default")
    
    def clear_all(self):
        """Clear all"""
        for part_data in self.leg_parts.values():
            self.renderer.RemoveActor(part_data["actor"])
        
        self.leg_parts.clear()
        self.parts_list.clear()
        self.color_index = 0
        
        self.vtk_widget.GetRenderWindow().Render()
        self.data_label.setText("No data loaded")
        self.data_label.setStyleSheet("color: #6e7681;")
        self.show_message("🗑️ All visualizations cleared")
        self.info_label.setText("🎯 Viewport: Ready for rendering")
    
    def show_message(self, message):
        """Display status message"""
        self.statusBar.showMessage(message, 5000)
        print(f"[INFO] {message}")
    
    def create_clipping_controls(self):
        """Create clipping controls (X and Y axes only)"""
        clip_group = QGroupBox("✂️ Clipping Controls")
        clip_layout = QVBoxLayout()
        clip_layout.setSpacing(10)
        
        # X-axis
        x_header = QHBoxLayout()
        self.x_clip_checkbox = QCheckBox("Enable X-Axis (Left ↔ Right)")
        self.x_clip_checkbox.setStyleSheet("color: #3fb950; font-weight: bold;")
        self.x_clip_checkbox.stateChanged.connect(lambda state: self.toggle_clipping('x', state == Qt.Checked))
        x_header.addWidget(self.x_clip_checkbox)
        
        self.x_invert_checkbox = QCheckBox("Invert")
        self.x_invert_checkbox.setEnabled(False)
        self.x_invert_checkbox.stateChanged.connect(lambda state: self.invert_clipping('x', state == Qt.Checked))
        x_header.addWidget(self.x_invert_checkbox)
        clip_layout.addLayout(x_header)
        
        x_container = QHBoxLayout()
        self.clip_x_slider = QSlider(Qt.Horizontal)
        self.clip_x_slider.setMinimum(-100)
        self.clip_x_slider.setMaximum(100)
        self.clip_x_slider.setValue(0)
        self.clip_x_slider.setEnabled(False)
        self.clip_x_slider.valueChanged.connect(lambda v: self.update_clipping('x', v))
        x_container.addWidget(self.clip_x_slider)
        
        self.clip_x_label = QLabel("0")
        self.clip_x_label.setMinimumWidth(40)
        self.clip_x_label.setAlignment(Qt.AlignCenter)
        self.clip_x_label.setStyleSheet("background: #21262d; border: 1px solid #30363d; border-radius: 4px; padding: 4px; color: #3fb950;")
        x_container.addWidget(self.clip_x_label)
        clip_layout.addLayout(x_container)
        
        separator1 = QFrame()
        separator1.setObjectName("separatorLine")
        clip_layout.addWidget(separator1)
        
        # Y-axis
        y_header = QHBoxLayout()
        self.y_clip_checkbox = QCheckBox("Enable Y-Axis (Front ↔ Back)")
        self.y_clip_checkbox.setStyleSheet("color: #58a6ff; font-weight: bold;")
        self.y_clip_checkbox.stateChanged.connect(lambda state: self.toggle_clipping('y', state == Qt.Checked))
        y_header.addWidget(self.y_clip_checkbox)
        
        self.y_invert_checkbox = QCheckBox("Invert")
        self.y_invert_checkbox.setEnabled(False)
        self.y_invert_checkbox.stateChanged.connect(lambda state: self.invert_clipping('y', state == Qt.Checked))
        y_header.addWidget(self.y_invert_checkbox)
        clip_layout.addLayout(y_header)
        
        y_container = QHBoxLayout()
        self.clip_y_slider = QSlider(Qt.Horizontal)
        self.clip_y_slider.setMinimum(-100)
        self.clip_y_slider.setMaximum(100)
        self.clip_y_slider.setValue(0)
        self.clip_y_slider.setEnabled(False)
        self.clip_y_slider.valueChanged.connect(lambda v: self.update_clipping('y', v))
        y_container.addWidget(self.clip_y_slider)
        
        self.clip_y_label = QLabel("0")
        self.clip_y_label.setMinimumWidth(40)
        self.clip_y_label.setAlignment(Qt.AlignCenter)
        self.clip_y_label.setStyleSheet("background: #21262d; border: 1px solid #30363d; border-radius: 4px; padding: 4px; color: #58a6ff;")
        y_container.addWidget(self.clip_y_label)
        clip_layout.addLayout(y_container)
        
        separator2 = QFrame()
        separator2.setObjectName("separatorLine")
        clip_layout.addWidget(separator2)
        
        # Control buttons
        clip_buttons = QHBoxLayout()
        clip_buttons.setSpacing(8)
        
        reset_clip_btn = QPushButton("🔄 Reset")
        reset_clip_btn.clicked.connect(self.reset_clipping)
        clip_buttons.addWidget(reset_clip_btn)
        
        self.disable_clip_btn = QPushButton("❌ Disable")
        self.disable_clip_btn.setObjectName("dangerButton")
        self.disable_clip_btn.clicked.connect(self.disable_clipping)
        clip_buttons.addWidget(self.disable_clip_btn)
        
        clip_layout.addLayout(clip_buttons)
        clip_group.setLayout(clip_layout)
        
        # Insert into control panel
        layout = self.control_panel_widget.layout()
        layout.insertWidget(layout.count() - 1, clip_group)
    
    def toggle_clipping(self, axis, checked):
        """Toggle clipping plane on/off for specific axis"""
        if not self.leg_parts:
            return
            
        if checked:
            if axis == 'x':
                normal = [1, 0, 0]
                origin = [0, 0, 0]
                self.clip_x_slider.setEnabled(True)
                self.x_invert_checkbox.setEnabled(True)
            elif axis == 'y':
                normal = [0, 1, 0]
                origin = [0, 0, 0]
                self.clip_y_slider.setEnabled(True)
                self.y_invert_checkbox.setEnabled(True)
            
            self.clip_planes[axis] = {'normal': normal, 'origin': origin, 'inverted': False}
            self.apply_clipping()
            self.show_message(f"✅ {axis.upper()}-axis clipping enabled")
        else:
            self.clip_planes[axis] = None
            if axis == 'x':
                self.clip_x_slider.setEnabled(False)
                self.x_invert_checkbox.setEnabled(False)
                self.x_invert_checkbox.setChecked(False)
            elif axis == 'y':
                self.clip_y_slider.setEnabled(False)
                self.y_invert_checkbox.setEnabled(False)
                self.y_invert_checkbox.setChecked(False)
            self.apply_clipping()
            self.show_message(f"❌ {axis.upper()}-axis clipping disabled")
    
    def update_clipping(self, axis, value):
        """Update clipping plane position"""
        if self.clip_planes[axis] is None:
            return
            
        position = value / 100.0 * 50  # Scale to reasonable range
        
        if axis == 'x':
            self.clip_planes[axis]['origin'] = [position, 0, 0]
            self.clip_x_label.setText(str(value))
        elif axis == 'y':
            self.clip_planes[axis]['origin'] = [0, position, 0]
            self.clip_y_label.setText(str(value))
        
        self.apply_clipping()
    
    def invert_clipping(self, axis, checked):
        """Invert clipping plane normal"""
        if self.clip_planes[axis] is None:
            return
            
        self.clip_planes[axis]['inverted'] = checked
        normal = self.clip_planes[axis]['normal']
        self.clip_planes[axis]['normal'] = [-n for n in normal]
        
        self.apply_clipping()
        self.show_message(f"🔄 {axis.upper()}-axis clipping {'inverted' if checked else 'normal'}")
    
    def apply_clipping(self):
        """Apply all active clipping planes to all leg parts"""
        if not self.leg_parts:
            return
        
        for filename, part_data in self.leg_parts.items():
            # Remove all existing clipping planes
            part_data["mapper"].RemoveAllClippingPlanes()
            
            # Add active clipping planes
            for axis, plane_data in self.clip_planes.items():
                if plane_data is not None:
                    clip_plane = vtk.vtkPlane()
                    clip_plane.SetNormal(plane_data['normal'])
                    clip_plane.SetOrigin(plane_data['origin'])
                    part_data["mapper"].AddClippingPlane(clip_plane)
        
        self.vtk_widget.GetRenderWindow().Render()
    
    def reset_clipping(self):
        """Reset all clipping planes"""
        if hasattr(self, 'clip_x_slider'):
            self.clip_x_slider.setValue(0)
            self.clip_y_slider.setValue(0)
            
            # Reset invert checkboxes
            if hasattr(self, 'x_invert_checkbox'):
                self.x_invert_checkbox.setChecked(False)
                self.y_invert_checkbox.setChecked(False)
            
            # Reset plane normals
            for axis in ['x', 'y']:
                if self.clip_planes[axis] is not None:
                    if axis == 'x':
                        self.clip_planes[axis]['normal'] = [1, 0, 0]
                    elif axis == 'y':
                        self.clip_planes[axis]['normal'] = [0, 1, 0]
                    self.clip_planes[axis]['origin'] = [0, 0, 0]
                    self.clip_planes[axis]['inverted'] = False
            
            self.apply_clipping()
            self.show_message("🔄 All clipping planes reset")
    
    def disable_clipping(self):
        """Disable all clipping"""
        if hasattr(self, 'clipping_enabled'):
            # Remove all clipping planes from all parts
            for part_data in self.leg_parts.values():
                part_data["mapper"].RemoveAllClippingPlanes()
            
            # Reset clip planes dictionary
            self.clip_planes = {'x': None, 'y': None}
            
            # Remove clipping control widget
            layout = self.control_panel_widget.layout()
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, QGroupBox) and "Clipping" in widget.title():
                        widget.deleteLater()
                        break
            
            delattr(self, 'clipping_enabled')
            self.show_message("✅ Clipping mode disabled")
            self.info_label.setText(f"🎯 Viewport: Rendering {len(self.leg_parts)} components")
            self.vtk_widget.GetRenderWindow().Render()


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show window
    window = LegVisualizationGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()