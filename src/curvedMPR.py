import sys
import numpy as np
import pydicom
import nibabel as nib
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QSlider, QLabel, 
                             QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
from scipy import ndimage
from scipy.interpolate import splprep, splev

# ============= Default Paths للأنظمة المدعومة فقط =============
DEFAULT_PATHS = {
    'nervous': {
        'type': 'nifti',
        'path': r"D:\brain.nii"
    },
    'dental': {
        'type': 'dicom',
        'path': r"D:\Datasets\Dental\Dental"
    }
}
# ====================================================

class DICOMViewer(QMainWindow):
    def __init__(self, system_type=None):
        super().__init__()
        # التأكد من أن النظام مدعوم (أو None لعدم تحميل داتا)
        if system_type not in ['nervous', 'dental', None]:
            print(f"Warning: System type '{system_type}' not recognized. Using manual loading mode.")
            system_type = None
            
        self.system_type = system_type
        self.volume = None
        self.current_slice = 0
        self.drawing = False
        self.curve_points = []
        self.curved_mpr = None
        self.last_point = None
        self.min_point_distance = 15
        self.mpr_thickness = 100
        self.view_side = 'concave'
        
        self.initUI()
        
        # حمل الـ default data حسب النظام
        if self.system_type is not None:
            self.auto_load_nifti()
        
    def initUI(self):
        # تحديد اسم النافذة حسب النظام
        window_titles = {
            'nervous': '🧠 Curved MPR - Nervous System',
            'dental': '🦷 Curved MPR - Dental System',
            None: 'Curved MPR Viewer'
        }
        
        self.setWindowTitle(window_titles.get(self.system_type, 'Curved MPR Viewer'))
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Original slice view
        left_panel = QVBoxLayout()
        
        # System indicator label
        system_names = {
            'nervous': '🧠 Nervous System',
            'dental': '🦷 Dental System',
            None: '📂 Manual Data Loading'
        }
        system_label = QLabel(f'System: {system_names.get(self.system_type, "Unknown")}')
        system_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        left_panel.addWidget(system_label)
        
        # Load buttons
        load_btn_layout = QHBoxLayout()
        self.load_dicom_btn = QPushButton('Load DICOM Folder')
        self.load_dicom_btn.clicked.connect(self.load_dicom)
        load_btn_layout.addWidget(self.load_dicom_btn)
        
        self.load_nifti_btn = QPushButton('Load NIfTI File')
        self.load_nifti_btn.clicked.connect(self.load_nifti)
        load_btn_layout.addWidget(self.load_nifti_btn)
        
        left_panel.addLayout(load_btn_layout)
        
        self.slice_label = QLabel('Slice: 0/0')
        left_panel.addWidget(self.slice_label)
        
        self.slice_slider = QSlider(Qt.Horizontal)
        self.slice_slider.setEnabled(False)
        self.slice_slider.valueChanged.connect(self.update_slice)
        left_panel.addWidget(self.slice_slider)
        
        self.slice_canvas = ImageCanvas(800, 800)
        self.slice_canvas.mouse_pressed.connect(self.start_drawing)
        self.slice_canvas.mouse_moved.connect(self.continue_drawing)
        self.slice_canvas.mouse_released.connect(self.end_drawing)
        left_panel.addWidget(self.slice_canvas)
        
        btn_layout = QHBoxLayout()
        self.clear_btn = QPushButton('Clear Curve')
        self.clear_btn.clicked.connect(self.clear_curve)
        self.clear_btn.setEnabled(False)
        
        self.generate_btn = QPushButton('Generate Curved MPR')
        self.generate_btn.clicked.connect(self.generate_curved_mpr)
        self.generate_btn.setEnabled(False)
        
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.generate_btn)
        left_panel.addLayout(btn_layout)
        
        # View side selection
        side_layout = QHBoxLayout()
        side_label = QLabel('View Side:')
        side_layout.addWidget(side_label)
        
        self.concave_btn = QPushButton('Concave (Inner)')
        self.concave_btn.clicked.connect(lambda: self.set_view_side('concave'))
        self.concave_btn.setStyleSheet("background-color: lightblue;")
        side_layout.addWidget(self.concave_btn)
        
        self.convex_btn = QPushButton('Convex (Outer)')
        self.convex_btn.clicked.connect(lambda: self.set_view_side('convex'))
        side_layout.addWidget(self.convex_btn)
        
        left_panel.addLayout(side_layout)
        
        # Thickness control
        thickness_layout = QHBoxLayout()
        self.thickness_label = QLabel(f'Thickness: {self.mpr_thickness}px')
        thickness_layout.addWidget(self.thickness_label)
        
        self.thickness_slider = QSlider(Qt.Horizontal)
        self.thickness_slider.setMinimum(20)
        self.thickness_slider.setMaximum(200)
        self.thickness_slider.setValue(self.mpr_thickness)
        self.thickness_slider.valueChanged.connect(self.update_thickness)
        thickness_layout.addWidget(self.thickness_slider)
        
        left_panel.addLayout(thickness_layout)
        
        # Right panel - Curved MPR view
        right_panel = QVBoxLayout()
        
        mpr_label = QLabel('Curved MPR Result')
        mpr_label.setAlignment(Qt.AlignCenter)
        right_panel.addWidget(mpr_label)
        
        self.mpr_canvas = ImageCanvas(800, 800)
        right_panel.addWidget(self.mpr_canvas)
        
        main_layout.addLayout(left_panel)
        main_layout.addLayout(right_panel)
    
    def auto_load_nifti(self):
        """حمل ملف NIfTI أو DICOM تلقائياً حسب نوع النظام"""
        # إذا كان None، لا تحمل أي داتا
        if self.system_type is None:
            print("Manual loading mode - please load data using the buttons")
            return
        
        config = DEFAULT_PATHS.get(self.system_type)
        
        if not config:
            print(f"Warning: No default configuration found for {self.system_type}")
            return
        
        data_type = config.get('type')
        file_path = config.get('path')
        
        if not file_path or not Path(file_path).exists():
            print(f"Warning: Default file not found for {self.system_type}: {file_path}")
            print("Please load a file manually or update the DEFAULT_PATHS dictionary")
            return
        
        try:
            if data_type == 'nifti':
                self._load_nifti_data(file_path)
            elif data_type == 'dicom':
                self._load_dicom_data(file_path)
            else:
                print(f"Unknown data type: {data_type}")
                return
            
            system_names = {
                'nervous': 'Nervous System',
                'dental': 'Dental System',
            }
            print(f"✓ Auto-loaded {system_names.get(self.system_type, 'Unknown')} data: {file_path}")
            print(f"Volume shape: {self.volume.shape}")
            
        except Exception as e:
            print(f"Failed to auto-load data for {self.system_type}: {str(e)}")
    
    def _load_nifti_data(self, file_path):
        """تحميل NIfTI data"""
        nifti_img = nib.load(file_path)
        volume_data = nifti_img.get_fdata()
        
        self.volume = np.array(volume_data, dtype=np.float64)
        
        if self.volume.ndim == 4:
            self.volume = self.volume[..., 0]
            print("4D volume detected, using first timepoint")
        elif self.volume.ndim != 3:
            print(f"Warning: Unsupported volume dimensions: {self.volume.ndim}D")
            return
        
        self.volume = ((self.volume - self.volume.min()) / 
                      (self.volume.max() - self.volume.min()) * 255.0)
        
        self.slice_slider.setMaximum(self.volume.shape[0] - 1)
        self.slice_slider.setValue(self.volume.shape[0] // 2)
        self.slice_slider.setEnabled(True)
        self.clear_btn.setEnabled(True)
        
        self.current_slice = self.volume.shape[0] // 2
        self.update_slice()
    
    def _load_dicom_data(self, folder_path):
        """تحميل DICOM data"""
        dicom_files = sorted(Path(folder_path).glob('*.dcm'))
        if not dicom_files:
            print(f"No DICOM files found in: {folder_path}")
            return
        
        slices = []
        for f in dicom_files:
            ds = pydicom.dcmread(str(f))
            slices.append(ds)
        
        slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
        
        self.volume = np.stack([s.pixel_array.astype(np.float64) for s in slices])
        
        self.volume = ((self.volume - self.volume.min()) / 
                      (self.volume.max() - self.volume.min()) * 255.0)
        
        self.slice_slider.setMaximum(len(slices) - 1)
        self.slice_slider.setValue(len(slices) // 2)
        self.slice_slider.setEnabled(True)
        self.clear_btn.setEnabled(True)
        
        self.current_slice = len(slices) // 2
        self.update_slice()
    
    def load_nifti(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select NIfTI File", 
            "", 
            "NIfTI Files (*.nii *.nii.gz);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            nifti_img = nib.load(file_path)
            volume_data = nifti_img.get_fdata()
            
            self.volume = np.array(volume_data, dtype=np.float64)
            
            if self.volume.ndim == 4:
                self.volume = self.volume[..., 0]
                QMessageBox.information(self, "Info", "4D volume detected, using first timepoint")
            elif self.volume.ndim != 3:
                QMessageBox.warning(self, "Error", f"Unsupported volume dimensions: {self.volume.ndim}D")
                return
            
            self.volume = ((self.volume - self.volume.min()) / 
                          (self.volume.max() - self.volume.min()) * 255.0)
            
            self.slice_slider.setMaximum(self.volume.shape[0] - 1)
            self.slice_slider.setValue(self.volume.shape[0] // 2)
            self.slice_slider.setEnabled(True)
            self.clear_btn.setEnabled(True)
            
            self.current_slice = self.volume.shape[0] // 2
            self.update_slice()
            
            QMessageBox.information(self, "Success", 
                                   f"Loaded NIfTI file\n"
                                   f"Volume shape: {self.volume.shape}")
            
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Error", 
                               f"Failed to load NIfTI: {str(e)}\n\n{traceback.format_exc()}")
    
    def load_dicom(self):
        folder = QFileDialog.getExistingDirectory(self, "Select DICOM Folder")
        if not folder:
            return
            
        try:
            dicom_files = sorted(Path(folder).glob('*.dcm'))
            if not dicom_files:
                QMessageBox.warning(self, "Error", "No DICOM files found in folder")
                return
            
            slices = []
            for f in dicom_files:
                ds = pydicom.dcmread(str(f))
                slices.append(ds)
            
            slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
            
            self.volume = np.stack([s.pixel_array.astype(np.float64) for s in slices])
            
            self.volume = ((self.volume - self.volume.min()) / 
                          (self.volume.max() - self.volume.min()) * 255.0)
            
            self.slice_slider.setMaximum(len(slices) - 1)
            self.slice_slider.setValue(len(slices) // 2)
            self.slice_slider.setEnabled(True)
            self.clear_btn.setEnabled(True)
            
            self.current_slice = len(slices) // 2
            self.update_slice()
            
            QMessageBox.information(self, "Success", 
                                   f"Loaded {len(slices)} DICOM slices\n"
                                   f"Volume shape: {self.volume.shape}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load DICOM: {str(e)}")
    
    def update_slice(self):
        if self.volume is None:
            return
        
        self.current_slice = self.slice_slider.value()
        self.slice_label.setText(f'Slice: {self.current_slice}/{self.volume.shape[0]-1}')
        
        slice_img = self.volume[self.current_slice].astype(np.uint8)
        self.slice_canvas.set_image(slice_img)
        
        if self.curve_points:
            self.slice_canvas.set_curve_points(self.curve_points)
    
    def start_drawing(self, pos):
        if self.volume is None:
            return
        self.drawing = True
        self.curve_points = [pos]
        self.last_point = pos
        self.slice_canvas.set_curve_points(self.curve_points)
        
    def continue_drawing(self, pos):
        if self.drawing and self.volume is not None:
            if self.last_point is not None:
                dx = pos.x() - self.last_point.x()
                dy = pos.y() - self.last_point.y()
                distance = np.sqrt(dx**2 + dy**2)
                
                if distance >= self.min_point_distance:
                    self.curve_points.append(pos)
                    self.last_point = pos
                    self.slice_canvas.set_curve_points(self.curve_points)
            else:
                self.curve_points.append(pos)
                self.last_point = pos
                self.slice_canvas.set_curve_points(self.curve_points)
    
    def end_drawing(self, pos):
        if self.drawing and self.volume is not None:
            self.drawing = False
            if len(self.curve_points) > 3:
                self.generate_btn.setEnabled(True)
    
    def clear_curve(self):
        self.curve_points = []
        self.last_point = None
        self.slice_canvas.set_curve_points([])
        self.generate_btn.setEnabled(False)
        self.mpr_canvas.clear()
    
    def set_view_side(self, side):
        self.view_side = side
        self.concave_btn.setStyleSheet("")
        self.convex_btn.setStyleSheet("")
        
        if side == 'concave':
            self.concave_btn.setStyleSheet("background-color: lightblue;")
        else:
            self.convex_btn.setStyleSheet("background-color: lightblue;")
    
    def update_thickness(self, value):
        self.mpr_thickness = value
        self.thickness_label.setText(f'Thickness: {value}px')
    
    def generate_curved_mpr(self):
        if len(self.curve_points) < 4:
            QMessageBox.warning(self, "Error", "Need at least 4 points for curved MPR")
            return
        
        try:
            points = np.array([[float(p.x()), float(p.y())] for p in self.curve_points], dtype=np.float64)
            
            h, w = self.volume[self.current_slice].shape
            scale_x = float(w) / float(self.slice_canvas.width())
            scale_y = float(h) / float(self.slice_canvas.height())
            points[:, 0] = points[:, 0] * scale_x
            points[:, 1] = points[:, 1] * scale_y
            
            tck, u = splprep([points[:, 0], points[:, 1]], s=len(points)*2, k=min(3, len(points)-1))
            
            u_new = np.linspace(0, 1, 500)
            x_new, y_new = splev(u_new, tck)
            x_new = np.asarray(x_new, dtype=np.float64)
            y_new = np.asarray(y_new, dtype=np.float64)
            
            dx = np.diff(x_new)
            dy = np.diff(y_new)
            lengths = np.sqrt(dx**2 + dy**2)
            lengths = np.maximum(lengths, 1e-6)
            
            tx = dx / lengths
            ty = dy / lengths
            
            tx = np.append(tx, tx[-1])
            ty = np.append(ty, ty[-1])
            
            if self.view_side == 'concave':
                nx = -ty
                ny = tx
            else:
                nx = ty
                ny = -tx
            
            num_depth_slices = self.volume.shape[0]
            
            mpr_width = len(x_new)
            mpr_height = self.mpr_thickness
            curved_mpr = np.zeros((num_depth_slices, mpr_height, mpr_width), dtype=np.float64)
            
            for i in range(len(x_new)):
                for j in range(mpr_height):
                    offset = float(j)
                    
                    sample_x = x_new[i] + nx[i] * offset
                    sample_y = y_new[i] + ny[i] * offset
                    
                    for z in range(num_depth_slices):
                        sample_z = float(z)
                        
                        if (0 <= sample_x < w-1 and 
                            0 <= sample_y < h-1 and 
                            0 <= sample_z < self.volume.shape[0]-1):
                            
                            x0, y0, z0 = int(sample_x), int(sample_y), int(sample_z)
                            x1, y1, z1 = x0 + 1, y0 + 1, z0 + 1
                            
                            x1 = min(x1, w - 1)
                            y1 = min(y1, h - 1)
                            z1 = min(z1, self.volume.shape[0] - 1)
                            
                            fx = sample_x - x0
                            fy = sample_y - y0
                            fz = sample_z - z0
                            
                            c000 = self.volume[z0, y0, x0]
                            c001 = self.volume[z0, y0, x1]
                            c010 = self.volume[z0, y1, x0]
                            c011 = self.volume[z0, y1, x1]
                            c100 = self.volume[z1, y0, x0]
                            c101 = self.volume[z1, y0, x1]
                            c110 = self.volume[z1, y1, x0]
                            c111 = self.volume[z1, y1, x1]
                            
                            c00 = c000 * (1 - fx) + c001 * fx
                            c01 = c010 * (1 - fx) + c011 * fx
                            c10 = c100 * (1 - fx) + c101 * fx
                            c11 = c110 * (1 - fx) + c111 * fx
                            
                            c0 = c00 * (1 - fy) + c01 * fy
                            c1 = c10 * (1 - fy) + c11 * fy
                            
                            value = c0 * (1 - fz) + c1 * fz
                            curved_mpr[z, j, i] = value
            
            curved_mpr_2d = np.max(curved_mpr, axis=1)
            
            self.curved_mpr = curved_mpr_2d.astype(np.uint8)
            self.mpr_canvas.set_image(self.curved_mpr)
            
            side_text = "Concave (Inner)" if self.view_side == 'concave' else "Convex (Outer)"
            QMessageBox.information(self, "Success", 
                                   f"Curved MPR generated\n"
                                   f"Size: {curved_mpr_2d.shape}\n"
                                   f"View: {side_text}\n"
                                   f"Thickness: {self.mpr_thickness}px")
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to generate MPR: {str(e)}\n\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Error", error_msg)


class ImageCanvas(QLabel):
    mouse_pressed = pyqtSignal(QPoint)
    mouse_moved = pyqtSignal(QPoint)
    mouse_released = pyqtSignal(QPoint)
    
    def __init__(self, width, height):
        super().__init__()
        self.setFixedSize(width, height)
        self.setStyleSheet("border: 1px solid black; background-color: black;")
        self.image = None
        self.curve_points = []
        
    def set_image(self, img_array):
        if img_array.dtype != np.uint8:
            img_array = img_array.astype(np.uint8)
        
        if not img_array.flags['C_CONTIGUOUS']:
            img_array = np.ascontiguousarray(img_array)
        
        h, w = img_array.shape
        bytes_per_line = w
        
        q_img = QImage(img_array.tobytes(), w, h, bytes_per_line, QImage.Format_Grayscale8)
        
        pixmap = QPixmap.fromImage(q_img).scaled(
            self.width(), self.height(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        if self.curve_points and len(self.curve_points) > 1:
            painter = QPainter(pixmap)
            pen = QPen(Qt.red, 3, Qt.SolidLine)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setRenderHint(QPainter.Antialiasing)
            
            for i in range(len(self.curve_points) - 1):
                painter.drawLine(self.curve_points[i], self.curve_points[i+1])
            
            painter.end()
        
        self.setPixmap(pixmap)
        self.image = img_array
    
    def set_curve_points(self, points):
        self.curve_points = points
        if self.image is not None:
            self.set_image(self.image)
    
    def clear(self):
        self.setPixmap(QPixmap())
        self.image = None
        self.curve_points = []
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_pressed.emit(event.pos())
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.mouse_moved.emit(event.pos())
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_released.emit(event.pos())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # قراءة system_type من command line arguments
    # استخدام None إذا لم يتم تحديد نظام (للتحميل اليدوي)
    if len(sys.argv) > 1:
        system_arg = sys.argv[1]
        system_type = system_arg if system_arg in ['nervous', 'dental'] else None
    else:
        system_type = None  # وضع التحميل اليدوي
    
    viewer = DICOMViewer(system_type=system_type)
    viewer.show()
    sys.exit(app.exec_())