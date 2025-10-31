import sys
import numpy as np
import pydicom
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QSlider, QLabel, 
                             QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import os
import nibabel as nib  # 🔥 مكتبة قراءة NIfTI



class OrthogonalPlaneViewer(QMainWindow):
    def __init__(self, system_id=None):
        super().__init__()
        self.volume = None
        self.vtk_volume = None
        self.plane_actors = []
        self.system_id = system_id
        
        # Define data paths for each system
        self.data_paths = {
            'cardio': r'D:\task2\chest dicom',
            'skeleton': r'D:\task2\leg scan dicom',
            'nervous': r'D:\task2\brain dicom',
        }
        
        self.initUI()
        
        # Auto-load data if system_id is provided
        if self.system_id and self.system_id in self.data_paths:
            self.auto_load_dicom()
        
    def initUI(self):
        title = '3D Orthogonal Plane DICOM Viewer'
        if self.system_id:
            title += f' - {self.system_id.capitalize()} System'
        
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Top controls
        top_layout = QHBoxLayout()
        
        self.load_btn = QPushButton('Load DICOM Folder')
        self.load_btn.clicked.connect(self.load_dicom)
        top_layout.addWidget(self.load_btn)
        
        self.reset_btn = QPushButton('Reset View')
        self.reset_btn.clicked.connect(self.reset_camera)
        self.reset_btn.setEnabled(False)
        top_layout.addWidget(self.reset_btn)
        
        # System label
        if self.system_id:
            system_label = QLabel(f'System: {self.system_id.upper()}')
            system_label.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 14px;")
            top_layout.addWidget(system_label)
        
        top_layout.addStretch()
        main_layout.addLayout(top_layout)
        
        # VTK Widget
        self.vtk_widget = QVTKRenderWindowInteractor(central_widget)
        main_layout.addWidget(self.vtk_widget)
        
        # Setup VTK renderer
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.1, 0.1, 0.1)
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        self.iren = self.vtk_widget.GetRenderWindow().GetInteractor()
        
        # Sliders for plane positions
        slider_layout = QHBoxLayout()
        
        # Axial slider (Blue - Z axis)
        axial_group = QVBoxLayout()
        self.axial_label = QLabel('Axial (Blue) - Slice: 0')
        self.axial_label.setStyleSheet("color: #4444FF; font-weight: bold;")
        axial_group.addWidget(self.axial_label)
        
        self.axial_slider = QSlider(Qt.Horizontal)
        self.axial_slider.setEnabled(False)
        self.axial_slider.valueChanged.connect(lambda: self.update_planes())
        axial_group.addWidget(self.axial_slider)
        slider_layout.addLayout(axial_group)
        
        # Coronal slider (Green - Y axis)
        coronal_group = QVBoxLayout()
        self.coronal_label = QLabel('Coronal (Green) - Slice: 0')
        self.coronal_label.setStyleSheet("color: #44FF44; font-weight: bold;")
        coronal_group.addWidget(self.coronal_label)
        
        self.coronal_slider = QSlider(Qt.Horizontal)
        self.coronal_slider.setEnabled(False)
        self.coronal_slider.valueChanged.connect(lambda: self.update_planes())
        coronal_group.addWidget(self.coronal_slider)
        slider_layout.addLayout(coronal_group)
        
        # Sagittal slider (Red - X axis)
        sagittal_group = QVBoxLayout()
        self.sagittal_label = QLabel('Sagittal (Red) - Slice: 0')
        self.sagittal_label.setStyleSheet("color: #FF4444; font-weight: bold;")
        sagittal_group.addWidget(self.sagittal_label)
        
        self.sagittal_slider = QSlider(Qt.Horizontal)
        self.sagittal_slider.setEnabled(False)
        self.sagittal_slider.valueChanged.connect(lambda: self.update_planes())
        sagittal_group.addWidget(self.sagittal_slider)
        slider_layout.addLayout(sagittal_group)
        
        main_layout.addLayout(slider_layout)
        
        # Initialize interactor
        self.iren.Initialize()
    
    def auto_load_dicom(self):
        """Automatically load DICOM data based on system_id"""
        if self.system_id not in self.data_paths:
            QMessageBox.warning(self, "Error", f"No data path configured for {self.system_id}")
            return
        
        folder = self.data_paths[self.system_id]
        
        # Check if path exists
        if not os.path.exists(folder):
            QMessageBox.warning(self, "Error", 
                              f"Data folder not found:\n{folder}\n\nPlease use 'Load DICOM Folder' to select manually.")
            return
        
        self.load_dicom_from_path(folder)
    
    def load_dicom(self):
        """Manual DICOM loading via file dialog"""
        folder = QFileDialog.getExistingDirectory(self, "Select DICOM Folder")
        if not folder:
            return
        
        self.load_dicom_from_path(folder)
    
    def load_dicom_from_path(self, folder):
        """Load DICOM files from specified path"""
        try:
            # Load all DICOM files
            dicom_files = sorted(Path(folder).glob('*.dcm'))
            if not dicom_files:
                QMessageBox.warning(self, "Error", "No DICOM files found in folder")
                return
            
            # Read all slices
            slices = []
            for f in dicom_files:
                ds = pydicom.dcmread(str(f))
                slices.append(ds)
            
            # Sort by slice location
            slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
            
            # Create 3D volume
            self.volume = np.stack([s.pixel_array.astype(np.float64) for s in slices])
            
            # Normalize to 0-255
            self.volume = ((self.volume - self.volume.min()) / 
                          (self.volume.max() - self.volume.min()) * 255.0)
            
            # Convert to VTK format
            self.create_vtk_volume()
            
            # Setup sliders
            self.axial_slider.setMaximum(self.volume.shape[0] - 1)
            self.axial_slider.setValue(self.volume.shape[0] // 2)
            self.axial_slider.setEnabled(True)
            
            self.coronal_slider.setMaximum(self.volume.shape[1] - 1)
            self.coronal_slider.setValue(self.volume.shape[1] // 2)
            self.coronal_slider.setEnabled(True)
            
            self.sagittal_slider.setMaximum(self.volume.shape[2] - 1)
            self.sagittal_slider.setValue(self.volume.shape[2] // 2)
            self.sagittal_slider.setEnabled(True)
            
            self.reset_btn.setEnabled(True)
            
            # Create the orthogonal planes
            self.update_planes()
            
            # Reset camera
            self.reset_camera()
            
            system_info = f" ({self.system_id.upper()})" if self.system_id else ""
            QMessageBox.information(self, "Success", 
                                   f"Loaded {len(slices)} slices{system_info}\n"
                                   f"Volume shape: {self.volume.shape}")
            
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Error", f"Failed to load DICOM: {str(e)}\n\n{traceback.format_exc()}")
    
    def create_vtk_volume(self):
        """Convert numpy array to VTK image data"""
        vtk_data = vtk.vtkImageData()
        vtk_data.SetDimensions(self.volume.shape[2], self.volume.shape[1], self.volume.shape[0])
        vtk_data.SetSpacing(1, 1, 1)
        vtk_data.SetOrigin(0, 0, 0)
        
        # Convert to VTK array
        flat_volume = self.volume.flatten(order='F')
        vtk_array = vtk.vtkFloatArray()
        vtk_array.SetNumberOfComponents(1)
        vtk_array.SetNumberOfTuples(flat_volume.size)
        for i, val in enumerate(flat_volume):
            vtk_array.SetValue(i, val)
        
        vtk_data.GetPointData().SetScalars(vtk_array)
        self.vtk_volume = vtk_data
        
    def update_planes(self):
        """Update all three orthogonal planes"""
        if self.vtk_volume is None:
            return
        
        # Remove all previous actors
        for actor in self.plane_actors:
            self.renderer.RemoveActor(actor)
        self.plane_actors.clear()
        
        dims = self.vtk_volume.GetDimensions()
        
        # Get slider values
        axial_idx = self.axial_slider.value()
        coronal_idx = self.coronal_slider.value()
        sagittal_idx = self.sagittal_slider.value()
        
        # Update labels
        self.axial_label.setText(f'Axial (Blue) - Slice: {axial_idx}/{dims[2]-1}')
        self.coronal_label.setText(f'Coronal (Green) - Slice: {coronal_idx}/{dims[1]-1}')
        self.sagittal_label.setText(f'Sagittal (Red) - Slice: {sagittal_idx}/{dims[0]-1}')
        
        # Create Axial plane (XY plane at Z position) - Blue
        axial_actor = self.create_image_plane(
            slice_idx=axial_idx,
            orientation='axial',
            color=(0.3, 0.3, 1.0)
        )
        self.plane_actors.append(axial_actor)
        
        # Create Coronal plane (XZ plane at Y position) - Green
        coronal_actor = self.create_image_plane(
            slice_idx=coronal_idx,
            orientation='coronal',
            color=(0.3, 1.0, 0.3)
        )
        self.plane_actors.append(coronal_actor)
        
        # Create Sagittal plane (YZ plane at X position) - Red
        sagittal_actor = self.create_image_plane(
            slice_idx=sagittal_idx,
            orientation='sagittal',
            color=(1.0, 0.3, 0.3)
        )
        self.plane_actors.append(sagittal_actor)
        
        self.vtk_widget.GetRenderWindow().Render()
    
    def create_image_plane(self, slice_idx, orientation, color):
        """Create a single image plane with texture"""
        
        # Extract 2D slice based on orientation
        if orientation == 'axial':
            slice_data = self.volume[slice_idx, :, :].astype(np.uint8)
        elif orientation == 'coronal':
            slice_data = self.volume[:, slice_idx, :].astype(np.uint8)
        else:  # sagittal
            slice_data = self.volume[:, :, slice_idx].astype(np.uint8)
        
        # Convert to VTK image
        height, width = slice_data.shape
        vtk_image = vtk.vtkImageData()
        vtk_image.SetDimensions(width, height, 1)
        
        vtk_array = vtk.vtkUnsignedCharArray()
        vtk_array.SetNumberOfComponents(1)
        vtk_array.SetNumberOfTuples(slice_data.size)
        for i, val in enumerate(slice_data.flatten()):
            vtk_array.SetValue(i, val)
        
        vtk_image.GetPointData().SetScalars(vtk_array)
        
        # Create texture
        texture = vtk.vtkTexture()
        texture.SetInputData(vtk_image)
        texture.InterpolateOn()
        
        # Create plane geometry
        plane = vtk.vtkPlaneSource()
        
        dims = self.vtk_volume.GetDimensions()
        
        if orientation == 'axial':
            plane.SetOrigin(0, 0, slice_idx)
            plane.SetPoint1(dims[0], 0, slice_idx)
            plane.SetPoint2(0, dims[1], slice_idx)
        elif orientation == 'coronal':
            plane.SetOrigin(0, slice_idx, 0)
            plane.SetPoint1(dims[0], slice_idx, 0)
            plane.SetPoint2(0, slice_idx, dims[2])
        else:  # sagittal
            plane.SetOrigin(slice_idx, 0, 0)
            plane.SetPoint1(slice_idx, dims[1], 0)
            plane.SetPoint2(slice_idx, 0, dims[2])
        
        # Add texture coordinates
        plane.Update()
        
        # Create mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(plane.GetOutputPort())
        
        # Create actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.SetTexture(texture)
        actor.GetProperty().SetOpacity(1.0)
        
        # Add colored border
        outline = vtk.vtkOutlineFilter()
        outline.SetInputConnection(plane.GetOutputPort())
        
        outline_mapper = vtk.vtkPolyDataMapper()
        outline_mapper.SetInputConnection(outline.GetOutputPort())
        
        outline_actor = vtk.vtkActor()
        outline_actor.SetMapper(outline_mapper)
        outline_actor.GetProperty().SetColor(color)
        outline_actor.GetProperty().SetLineWidth(4)
        
        # Add to renderer
        self.renderer.AddActor(actor)
        self.renderer.AddActor(outline_actor)
        
        # Store outline actor as well
        self.plane_actors.append(outline_actor)
        
        return actor
    
    def reset_camera(self):
        """Reset camera to default view"""
        if self.vtk_volume:
            self.renderer.ResetCamera()
            camera = self.renderer.GetActiveCamera()
            camera.Azimuth(45)
            camera.Elevation(30)
            camera.Zoom(1.2)
            self.renderer.ResetCameraClippingRange()
            self.vtk_widget.GetRenderWindow().Render()
    
    def closeEvent(self, event):
        self.vtk_widget.Finalize()
        event.accept()


if __name__ == '__main__':
    # Get system_id from command line arguments if provided
    system_id = None
    if len(sys.argv) > 1:
        system_id = sys.argv[1]
    
    app = QApplication(sys.argv)
    viewer = OrthogonalPlaneViewer(system_id)
    viewer.show()
    sys.exit(app.exec_())