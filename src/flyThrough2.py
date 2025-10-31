import sys
import os
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QFileDialog, QLabel, QHBoxLayout, 
                             QSlider, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from vispy import app, scene
from vispy.scene import transforms
import vtk
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


class FlythroughWindow(QMainWindow):
    def __init__(self, system_type=None, parts_data=None):
        super().__init__()
        
        # 🔥 استقبال البيانات من الـ GUI
        self.system_type = system_type  # "heart", "leg", "brain", "dental" or None
        self.parts_data = parts_data    # الـ parts dictionary من النافذة الأصلية
        
        # Setup UI (التصميم الأصلي)
        self.setup_original_ui()
        
        # 🔥 تحميل الداتا لو موجودة
        if self.parts_data:
            self.load_received_parts()
    
    def setup_original_ui(self):
        """Setup the original UI design"""
        # Set title based on system type
        title_map = {
            'heart': '❤️ Heart Model Navigator',
            'brain': '🧠 Brain Model Navigator',
            'leg': '🦵 Leg Model Navigator',
            'dental': '🦷 Dental Model Navigator'
        }
        window_title = title_map.get(self.system_type, '3D Model Navigator')
        self.setWindowTitle(window_title)
        self.setGeometry(100, 100, 1200, 900)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Instructions label
        instructions = QLabel(
            "Controls:\n"
            "+ : Zoom In  |  - : Zoom Out  |  Space: Move Forward  |  Ctrl: Move Backward\n"
            "↑ : Move Up  |  ↓ : Move Down  |  → : Move Right  |  ← : Move Left\n"
            "Click + Drag: Rotate View"
        )
        instructions.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(instructions)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Load button
        load_text_map = {
            'heart': '📄 Load Heart Model (.obj)',
            'brain': '📄 Load Brain Model (.obj)',
            'leg': '📄 Load Leg Model (.obj)',
            'dental': '📄 Load Dental Model (.obj)'
        }
        load_text = load_text_map.get(self.system_type, '📄 Load 3D Model (.obj)')
        
        self.load_btn = QPushButton(load_text)
        self.load_btn.clicked.connect(self.load_model)
        button_layout.addWidget(self.load_btn)
        
        layout.addLayout(button_layout)
        
        # Flythrough controls group
        flythrough_group = QGroupBox("Flythrough Controls")
        flythrough_layout = QVBoxLayout()
        
        # End point controls
        endpoint_layout = QHBoxLayout()
        self.set_endpoint_btn = QPushButton("Set End Point (Current View)")
        self.set_endpoint_btn.clicked.connect(self.set_end_point)
        self.set_endpoint_btn.setEnabled(False)
        self.set_endpoint_btn.setStyleSheet("background-color: #FFE4B5;")
        endpoint_layout.addWidget(self.set_endpoint_btn)
        
        self.endpoint_label = QLabel("End Point: Not Set")
        self.endpoint_label.setStyleSheet("padding: 5px; font-size: 10px;")
        endpoint_layout.addWidget(self.endpoint_label)
        flythrough_layout.addLayout(endpoint_layout)
        
        # Auto flythrough button
        flythrough_btn_layout = QHBoxLayout()
        self.flythrough_btn = QPushButton("Start Auto Flythrough")
        self.flythrough_btn.clicked.connect(self.toggle_flythrough)
        self.flythrough_btn.setEnabled(False)
        flythrough_btn_layout.addWidget(self.flythrough_btn)
        flythrough_layout.addLayout(flythrough_btn_layout)
        
        # Speed slider
        speed_label = QLabel("Flythrough Speed:")
        speed_label.setStyleSheet("padding: 5px; margin-top: 10px;")
        flythrough_layout.addWidget(speed_label)
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(10)
        self.speed_slider.setMaximum(200)
        self.speed_slider.setValue(100)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(20)
        self.speed_slider.valueChanged.connect(self.update_speed)
        flythrough_layout.addWidget(self.speed_slider)
        
        self.speed_value_label = QLabel("Speed: 100%")
        self.speed_value_label.setStyleSheet("padding: 5px;")
        self.speed_value_label.setAlignment(Qt.AlignCenter)
        flythrough_layout.addWidget(self.speed_value_label)
        
        flythrough_group.setLayout(flythrough_layout)
        layout.addWidget(flythrough_group)
        
        # VisPy canvas for 3D visualization
        self.canvas = scene.SceneCanvas(keys='interactive', show=False)
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.TurntableCamera(fov=45, distance=10)
        
        layout.addWidget(self.canvas.native)
        
        # Navigation parameters
        self.zoom_speed = 0.5
        self.move_speed = 0.3
        self.rotate_speed = 5
        
        self.mesh = None
        self.canvas.events.key_press.connect(self.on_key_press)
        self.canvas.events.mouse_press.connect(self.on_mouse_press)
        self.canvas.events.mouse_move.connect(self.on_mouse_move)
        self.canvas.events.mouse_release.connect(self.on_mouse_release)
        
        self.mouse_pressed = False
        self.last_mouse_pos = None
        self.mouse_button = None
        
        # Flythrough animation parameters
        self.flythrough_active = False
        self.flythrough_timer = QTimer()
        self.flythrough_timer.timeout.connect(self.update_flythrough)
        self.animation_time = 0
        self.base_animation_speed = 0.05
        self.animation_speed = self.base_animation_speed
        self.model_center = np.array([0, 0, 0])
        self.model_size = 1.0
        
        # End point for flythrough
        self.end_point = None
        self.start_point = None
        self.use_endpoint = False
    
    def get_color_for_part(self, filename):
        """
        🎨 اختيار اللون المناسب لكل جزء حسب النظام واسم الملف
        """
        filename_lower = filename.lower()
        
        # ❤️ HEART SYSTEM COLORS
        if self.system_type == 'heart':
            if any(kw in filename_lower for kw in ['ventricle', 'atrium', 'chamber', 'myocardium', 'muscle']):
                return (0.70, 0.17, 0.17, 1)  # أحمر غامق للعضلة القلبية
            elif any(kw in filename_lower for kw in ['artery', 'aorta', 'arterial']):
                return (0.90, 0.15, 0.15, 1)  # أحمر فاتح للشرايين
            elif any(kw in filename_lower for kw in ['vein', 'venous', 'vena']):
                return (0.20, 0.30, 0.65, 1)  # أزرق للأوردة
            elif any(kw in filename_lower for kw in ['valve', 'leaflet']):
                return (0.92, 0.88, 0.85, 1)  # أبيض كريمي للصمامات
            else:
                return (0.72, 0.26, 0.26, 1)  # أحمر قلبي افتراضي
        
        # 🧠 BRAIN SYSTEM COLORS
        elif self.system_type == 'brain':
            if any(kw in filename_lower for kw in ['cortex', 'gray', 'matter']):
                return (0.75, 0.68, 0.70, 1)  # رمادي وردي للقشرة
            elif any(kw in filename_lower for kw in ['white', 'corpus']):
                return (0.95, 0.93, 0.90, 1)  # أبيض للمادة البيضاء
            elif any(kw in filename_lower for kw in ['cerebellum']):
                return (0.70, 0.62, 0.65, 1)  # وردي داكن للمخيخ
            elif any(kw in filename_lower for kw in ['artery', 'arterial']):
                return (0.90, 0.15, 0.15, 1)  # أحمر للشرايين
            elif any(kw in filename_lower for kw in ['vein', 'venous']):
                return (0.20, 0.30, 0.70, 1)  # أزرق للأوردة
            else:
                return (0.75, 0.68, 0.70, 1)  # لون دماغي افتراضي
        
        # 🦵 LEG SYSTEM COLORS
        elif self.system_type == 'leg':
            if any(kw in filename_lower for kw in ['bone', 'femur', 'tibia', 'fibula', 'skeleton']):
                return (0.95, 0.92, 0.88, 1)  # عاجي للعظام
            elif any(kw in filename_lower for kw in ['muscle', 'gastrocnemius', 'quadriceps']):
                return (0.75, 0.28, 0.28, 1)  # أحمر عضلي
            elif any(kw in filename_lower for kw in ['tendon', 'ligament']):
                return (0.92, 0.88, 0.82, 1)  # بيج للأوتار
            elif any(kw in filename_lower for kw in ['fat', 'adipose']):
                return (0.96, 0.90, 0.70, 1)  # أصفر للدهون
            elif any(kw in filename_lower for kw in ['cartilage']):
                return (0.85, 0.90, 0.92, 1)  # أزرق فاتح للغضاريف
            else:
                return (0.72, 0.26, 0.26, 1)  # أحمر عضلي افتراضي
        
        # 🦷 DENTAL SYSTEM COLORS
        elif self.system_type == 'dental':
            if any(kw in filename_lower for kw in ['tooth', 'teeth', 'incisor', 'molar']):
                return (0.98, 0.97, 0.94, 1)  # أبيض ناصع للأسنان
            elif any(kw in filename_lower for kw in ['gum', 'gingiva']):
                return (0.92, 0.60, 0.65, 1)  # وردي للثة
            elif any(kw in filename_lower for kw in ['bone', 'jaw', 'alveolar']):
                return (0.94, 0.91, 0.86, 1)  # عظمي فاتح
            elif any(kw in filename_lower for kw in ['pulp']):
                return (0.85, 0.35, 0.35, 1)  # أحمر للعصب
            else:
                return (0.98, 0.97, 0.94, 1)  # أبيض أسنان افتراضي
        
        # ⚪ DEFAULT - لو مش معروف النظام
        else:
            return (0.8, 0.8, 0.8, 1)  # رمادي فاتح
    
    def load_received_parts(self):
        """Load the 3D parts that were sent from the parent window with proper colors"""
        if not self.parts_data:
            print("⚠️ No parts data to load")
            return
        
        print(f"\n{'='*60}")
        print(f"📦 Loading {self.system_type.upper() if self.system_type else 'MODEL'} Data into Flythrough")
        print(f"{'='*60}")
        
        all_vertices = []
        all_faces = []
        all_colors = []  # 🎨 إضافة قائمة الألوان
        vertex_offset = 0
        
        loaded_count = 0
        for filename, part_info in self.parts_data.items():
            try:
                # Get VTK polydata
                polydata = part_info['data']
                
                # Extract vertices
                points = polydata.GetPoints()
                num_points = points.GetNumberOfPoints()
                vertices = np.zeros((num_points, 3), dtype=np.float32)
                for i in range(num_points):
                    vertices[i] = points.GetPoint(i)
                
                # Extract faces
                cells = polydata.GetPolys()
                cells.InitTraversal()
                id_list = vtk.vtkIdList()
                faces = []
                
                while cells.GetNextCell(id_list):
                    if id_list.GetNumberOfIds() == 3:
                        faces.append([
                            id_list.GetId(0) + vertex_offset,
                            id_list.GetId(1) + vertex_offset,
                            id_list.GetId(2) + vertex_offset
                        ])
                
                # 🎨 الحصول على اللون المناسب لهذا الجزء
                color = self.get_color_for_part(filename)
                
                # إضافة اللون لكل vertex في هذا الجزء
                part_colors = np.tile(color, (num_points, 1))
                
                all_vertices.append(vertices)
                all_faces.extend(faces)
                all_colors.append(part_colors)
                vertex_offset += num_points
                
                loaded_count += 1
                color_str = f"RGBA({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f}, {color[3]:.2f})"
                print(f"  ✓ {filename} - Color: {color_str}")
                
            except Exception as e:
                print(f"  ✗ Failed to load {filename}: {e}")
        
        if loaded_count > 0:
            # Combine all vertices, faces, and colors
            combined_vertices = np.vstack(all_vertices)
            combined_faces = np.array(all_faces, dtype=np.uint32)
            combined_colors = np.vstack(all_colors)  # 🎨 دمج الألوان
            
            print(f"{'='*60}")
            print(f"✅ Successfully loaded {loaded_count}/{len(self.parts_data)} parts")
            print(f"📊 Total vertices: {len(combined_vertices)}, Total faces: {len(combined_faces)}")
            print(f"🎨 Colors applied per part based on {self.system_type.upper()} system")
            print(f"{'='*60}\n")
            
            # 🎨 Create mesh with vertex colors
            self.mesh = scene.visuals.Mesh(
                vertices=combined_vertices,
                faces=combined_faces,
                vertex_colors=combined_colors,  # 🔥 استخدام الألوان المخصصة
                shading='smooth'
            )
            
            self.view.add(self.mesh)
            
            # Calculate bounds and center camera
            min_bounds = combined_vertices.min(axis=0)
            max_bounds = combined_vertices.max(axis=0)
            self.model_center = (min_bounds + max_bounds) / 2
            self.view.camera.center = self.model_center
            
            # Adjust camera distance based on model size
            self.model_size = np.linalg.norm(max_bounds - min_bounds)
            self.view.camera.distance = self.model_size * 2
            
            self.canvas.show()
            self.load_btn.setText(f"Model Loaded ({loaded_count} parts)")
            self.flythrough_btn.setEnabled(True)
            self.set_endpoint_btn.setEnabled(True)
            print("✅ Model loaded successfully in Flythrough with proper colors!")
    
    def load_obj_file(self, file_path):
        """Load OBJ file with basic geometry only"""
        vertices = []
        faces = []
        
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if not parts:
                    continue
                
                # Vertex (only x, y, z coordinates)
                if parts[0] == 'v':
                    vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                
                # Face (can be triangles or quads)
                elif parts[0] == 'f':
                    face_vertices = []
                    for i in range(1, len(parts)):
                        vertex_index = parts[i].split('/')[0]
                        face_vertices.append(int(vertex_index) - 1)
                    
                    # Triangulate if needed
                    if len(face_vertices) == 3:
                        faces.append(face_vertices)
                    elif len(face_vertices) == 4:
                        faces.append([face_vertices[0], face_vertices[1], face_vertices[2]])
                        faces.append([face_vertices[0], face_vertices[2], face_vertices[3]])
                    elif len(face_vertices) > 4:
                        for i in range(1, len(face_vertices) - 1):
                            faces.append([face_vertices[0], face_vertices[i], face_vertices[i + 1]])
        
        vertices_array = np.array(vertices, dtype=np.float32)
        faces_array = np.array(faces, dtype=np.uint32)
        
        return vertices_array, faces_array
    
    def load_model(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select 3D Model", 
            "", 
            "OBJ Files (*.obj);;All Files (*)"
        )
        
        if file_path:
            try:
                vertices, faces = self.load_obj_file(file_path)
                
                print(f"Loaded {len(vertices)} vertices and {len(faces)} faces")
                
                # Remove old mesh if exists
                if self.mesh is not None:
                    self.mesh.parent = None
                
                # Determine default color based on system type
                color_map = {
                    'heart': (0.8, 0.3, 0.3, 1),      # Red for heart
                    'brain': (0.75, 0.68, 0.70, 1),   # Pinkish gray for brain
                    'leg': (0.72, 0.26, 0.26, 1),     # Muscle red for leg
                    'dental': (0.98, 0.97, 0.94, 1)   # White for teeth
                }
                default_color = color_map.get(self.system_type, (0.8, 0.8, 0.8, 1))
                
                self.mesh = scene.visuals.Mesh(
                    vertices=vertices,
                    faces=faces,
                    color=default_color,
                    shading='smooth'
                )
                
                self.view.add(self.mesh)
                
                # Calculate bounds and center camera
                min_bounds = vertices.min(axis=0)
                max_bounds = vertices.max(axis=0)
                self.model_center = (min_bounds + max_bounds) / 2
                self.view.camera.center = self.model_center
                
                # Adjust camera distance based on model size
                self.model_size = np.linalg.norm(max_bounds - min_bounds)
                self.view.camera.distance = self.model_size * 2
                
                self.canvas.show()
                self.load_btn.setText("Model Loaded - Load Another")
                self.flythrough_btn.setEnabled(True)
                self.set_endpoint_btn.setEnabled(True)
                print("Model loaded successfully!")
                
            except Exception as e:
                print(f"Error loading model: {e}")
                import traceback
                traceback.print_exc()
    
    def get_camera_state(self):
        """Get current camera state as a dictionary"""
        cam = self.view.camera
        return {
            'center': np.array(cam.center),
            'distance': cam.distance,
            'azimuth': cam.azimuth,
            'elevation': cam.elevation,
            'fov': cam.fov
        }
    
    def set_camera_state(self, state):
        """Set camera to a specific state"""
        cam = self.view.camera
        cam.center = state['center']
        cam.distance = state['distance']
        cam.azimuth = state['azimuth']
        cam.elevation = state['elevation']
        cam.fov = state['fov']
        self.canvas.update()
    
    def set_end_point(self):
        """Set the end point of the flythrough to current camera position"""
        if self.mesh is None:
            return
        
        self.end_point = self.get_camera_state()
        self.use_endpoint = True
        self.endpoint_label.setText("End Point: Set ✓")
        self.endpoint_label.setStyleSheet("padding: 5px; font-size: 10px; color: green; font-weight: bold;")
        print("End point set to current view")
    
    def update_speed(self, value):
        """Update animation speed based on slider value"""
        self.animation_speed = self.base_animation_speed * (value / 100.0)
        self.speed_value_label.setText(f"Speed: {value}%")
    
    def toggle_flythrough(self):
        """Toggle automatic flythrough animation"""
        if self.flythrough_active:
            self.stop_flythrough()
        else:
            self.start_flythrough()
    
    def start_flythrough(self):
        """Start the automatic flythrough animation"""
        self.flythrough_active = True
        self.animation_time = 0
        
        # Store starting point
        self.start_point = self.get_camera_state()
        
        self.flythrough_btn.setText("Stop Auto Flythrough")
        self.flythrough_timer.start(16)
        print("Flythrough started")
    
    def stop_flythrough(self):
        """Stop the automatic flythrough animation"""
        self.flythrough_active = False
        self.flythrough_timer.stop()
        self.flythrough_btn.setText("Start Auto Flythrough")
        print("Flythrough stopped")
    
    def interpolate_angle(self, start, end, t):
        """Interpolate between two angles, taking shortest path"""
        diff = end - start
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        return start + diff * t
    
    def update_flythrough(self):
        """Update camera position for flythrough animation"""
        if self.mesh is None:
            return
        
        cam = self.view.camera
        t = self.animation_time
        
        if self.use_endpoint and self.end_point is not None:
            # Interpolate from start to end point
            duration = 10.0
            progress = min(t / duration, 1.0)
            
            # Apply smooth easing
            eased_progress = progress * progress * (3.0 - 2.0 * progress)
            
            # Interpolate camera parameters
            cam.center = self.start_point['center'] * (1 - eased_progress) + self.end_point['center'] * eased_progress
            cam.distance = self.start_point['distance'] * (1 - eased_progress) + self.end_point['distance'] * eased_progress
            cam.azimuth = self.interpolate_angle(self.start_point['azimuth'], self.end_point['azimuth'], eased_progress)
            cam.elevation = self.interpolate_angle(self.start_point['elevation'], self.end_point['elevation'], eased_progress)
            cam.fov = self.start_point['fov'] * (1 - eased_progress) + self.end_point['fov'] * eased_progress
            
            # Stop when reaching end point
            if progress >= 1.0:
                self.stop_flythrough()
                print("Reached end point!")
        else:
            # Original automatic flythrough behavior
            azimuth = t * 30
            elevation = 15 * np.sin(t * 0.5) + 10
            base_distance = self.model_size * 2
            distance_variation = self.model_size * 0.8 * np.sin(t * 0.3)
            distance = base_distance + distance_variation
            fov = 45 + 10 * np.sin(t * 0.4)
            
            cam.azimuth = azimuth
            cam.elevation = elevation
            cam.distance = distance
            cam.fov = fov
            cam.center = self.model_center
        
        # Increment animation time
        self.animation_time += self.animation_speed
        
        # Update canvas
        self.canvas.update()
    
    def on_key_press(self, event):
        if self.mesh is None:
            return
        
        # Stop flythrough if user takes manual control
        if self.flythrough_active:
            self.stop_flythrough()
        
        cam = self.view.camera
        
        # Zoom controls
        if event.text == '+' or event.text == '=':
            cam.distance *= (1 - self.zoom_speed * 0.1)
        elif event.text == '-' or event.text == '_':
            cam.distance *= (1 + self.zoom_speed * 0.1)
        
        # Forward/Backward movement
        elif event.key == 'Space':
            cam.distance *= 0.9
        elif event.key == 'Control':
            cam.distance *= 1.1
        
        # Rotation controls (arrow keys)
        elif event.key == 'Up':
            cam.elevation += self.rotate_speed
        elif event.key == 'Down':
            cam.elevation -= self.rotate_speed
        elif event.key == 'Right':
            cam.azimuth -= self.rotate_speed
        elif event.key == 'Left':
            cam.azimuth += self.rotate_speed
        
        self.canvas.update()
    
    def on_mouse_press(self, event):
        # Stop flythrough if user takes manual control
        if self.flythrough_active:
            self.stop_flythrough()
        
        self.mouse_pressed = True
        self.last_mouse_pos = event.pos
        self.mouse_button = event.button
    
    def on_mouse_move(self, event):
        if not self.mouse_pressed or self.mesh is None:
            return
        
        if self.last_mouse_pos is None:
            self.last_mouse_pos = event.pos
            return
        
        cam = self.view.camera
        dx = event.pos[0] - self.last_mouse_pos[0]
        dy = event.pos[1] - self.last_mouse_pos[1]
        
        cam.azimuth -= dx * 0.5
        cam.elevation += dy * 0.5
        
        self.last_mouse_pos = event.pos
        self.canvas.update()
    
    def on_mouse_release(self, event):
        self.mouse_pressed = False
        self.last_mouse_pos = None
        self.mouse_button = None


def main():
    qt_app = QApplication(sys.argv)
    
    # Check if data was passed via command line
    system_type = None
    if len(sys.argv) >= 2:
        system_type = sys.argv[1]
        print(f"🚀 Launching Flythrough for {system_type.upper()} system")
    
    navigator = FlythroughWindow(system_type=system_type, parts_data=None)
    navigator.show()
    sys.exit(qt_app.exec_())


if __name__ == '__main__':
    main()