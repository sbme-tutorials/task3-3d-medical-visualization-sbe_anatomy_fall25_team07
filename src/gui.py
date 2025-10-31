import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import os

class MedicalSystemsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Medical Systems")
        self.root.geometry("450x400")
        self.root.configure(bg="#f0f4f8")
        
        # Create main frame
        main_frame = tk.Frame(root, padx=20, pady=20, bg="#f0f4f8")
        main_frame.pack(expand=True)
        
        # Title label
        title_label = tk.Label(main_frame, text="🏥 Medical Systems", 
                              font=("Arial", 18, "bold"),
                              bg="#f0f4f8", fg="#2c3e50")
        title_label.pack(pady=20)
        
        # Define systems with emojis and colors
        systems = [
            {"name": "❤️ Cardio System", "color": "#e74c3c", "hover": "#c0392b", "system_id": "cardio"},
            {"name": "🦴 Skeleton Muscular System", "color": "#3498db", "hover": "#2980b9", "system_id": "skeleton"},
            {"name": "🧠 Nervous System", "color": "#9b59b6", "hover": "#8e44ad", "system_id": "nervous"},
            {"name": "🦷 Dental", "color": "#1abc9c", "hover": "#16a085", "system_id": "dental"}
        ]
        
        # Create buttons for each system
        for system in systems:
            btn = tk.Button(main_frame, text=system["name"], 
                          command=lambda s=system: self.open_system_window(s),
                          width=28, height=2, 
                          font=("Arial", 12, "bold"),
                          bg=system["color"],
                          fg="white",
                          activebackground=system["hover"],
                          activeforeground="white",
                          relief=tk.RAISED,
                          bd=3,
                          cursor="hand2")
            btn.pack(pady=12)
            
            # Add hover effect
            btn.bind("<Enter>", lambda e, b=btn, c=system["hover"]: b.config(bg=c))
            btn.bind("<Leave>", lambda e, b=btn, c=system["color"]: b.config(bg=c))
    
    def open_system_window(self, system_info):
        system_name = system_info["name"]
        system_color = system_info["color"]
        system_id = system_info["system_id"]
        
        # Create new window for the selected system
        system_window = tk.Toplevel(self.root)
        system_window.title(system_name)
        system_window.geometry("550x450")
        system_window.configure(bg="#f0f4f8")
        
        # Create header frame with system color
        header_frame = tk.Frame(system_window, bg=system_color, height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Title for the system
        system_label = tk.Label(header_frame, text=system_name, 
                               font=("Arial", 16, "bold"),
                               bg=system_color, fg="white")
        system_label.pack(expand=True)
        
        # Create frame for buttons
        button_frame = tk.Frame(system_window, padx=20, pady=20, bg="#f0f4f8")
        button_frame.pack(fill=tk.BOTH, expand=True)
        
        # Define buttons based on the system
        if "Cardio" in system_name:
            button_configs = [
                {"name": "❤️ Surface Rendering & Navigation Methods", "color": "#e74c3c", "action": "heart_viz"},
                {"name": "✂️ Clipping Planes", "color": "#c0392b", "action": "clipping_planes", "system": system_id}
            ]
        elif "Skeleton" in system_name:
            button_configs = [
                {"name": "🦴💪 Surface Rendering & Navigation Methods", "color": "#3498db", "action": "legs_viz"},
                {"name": "✂️ Clipping Planes", "color": "#2980b9", "action": "clipping_planes", "system": system_id}
            ]
        elif "Nervous" in system_name:
            button_configs = [
                {"name": "🧠 Surface Rendering & Navigation Methods", "color": "#9b59b6", "action": "brain_viz"},
                {"name": "✂️ Clipping Planes", "color": "#8e44ad", "action": "clipping_planes", "system": system_id},
                {"name": "📐 Curved MPR", "color": "#71368a", "action": "curved_mpr", "system": system_id}
            ]
        elif "Dental" in system_name:
            button_configs = [
                {"name": "🦷 Surface Rendering & Navigation Methods ", "color": "#1abc9c", "action": "dental_viz"},
                {"name": "📐 Curved MPR", "color": "#16a085", "action": "curved_mpr", "system": system_id}
            ]
        
        for btn_config in button_configs:
            btn = tk.Button(button_frame, text=btn_config["name"],
                          command=lambda b=btn_config: self.button_action(b["name"], b["action"], system_window, b.get("system")),
                          width=35, height=2,
                          font=("Arial", 11),
                          bg=btn_config["color"],
                          fg="white",
                          activebackground=btn_config["color"],
                          activeforeground="white",
                          relief=tk.RAISED,
                          bd=2,
                          cursor="hand2")
            btn.pack(pady=8)
        
        # Create status bar at the bottom
        status_bar = tk.Label(system_window, text=f"{system_name} - Ready ✓", 
                            bd=1, relief=tk.SUNKEN, anchor=tk.W,
                            bg=system_color, fg="white",
                            font=("Arial", 9),
                            padx=5, pady=3)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        system_window.status_bar = status_bar
    
    def button_action(self, button_name, action, window, system_id=None):
        window.status_bar.config(text=f"{button_name} clicked ✓")
        print(f"{button_name} was clicked")
        
        # Launch heart visualization
        if action == "heart_viz":
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                heart_gui_path = os.path.join(current_dir, "heart_gui.py")
                
                subprocess.Popen([sys.executable, heart_gui_path])
                print("✓ Launched Heart Visualization System")
            except Exception as e:
                print(f"Error launching heart visualization: {e}")
                window.status_bar.config(text=f"❌ Error: {str(e)}")
        
        # Launch brain visualization
        elif action == "brain_viz":
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                brain_gui_path = os.path.join(current_dir, "brain_gui.py")
                
                subprocess.Popen([sys.executable, brain_gui_path])
                print("✓ Launched Brain Visualization System")
            except Exception as e:
                print(f"Error launching brain visualization: {e}")
                window.status_bar.config(text=f"❌ Error: {str(e)}")

        # Launch dental visualization
        elif action == "dental_viz":
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                dental_gui_path = os.path.join(current_dir, "teeth_gui.py")
                
                subprocess.Popen([sys.executable, dental_gui_path])
                print("✓ Launched Dental Visualization System")
            except Exception as e:
                print(f"Error launching Dental visualization: {e}")
                window.status_bar.config(text=f"❌ Error: {str(e)}")
        
        # Launch legs visualization
        elif action == "legs_viz":
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                legs_gui_path = os.path.join(current_dir, "legs_gui.py")
                
                subprocess.Popen([sys.executable, legs_gui_path])
                print("✓ Launched Muscelurskeleton Visualization System")
            except Exception as e:
                print(f"Error launching Muscelurskeleton visualization: {e}")
                window.status_bar.config(text=f"❌ Error: {str(e)}")
    
        # Launch clipping planes viewer
        elif action == "clipping_planes" and system_id:
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                clipping_path = os.path.join(current_dir, "clippingPlanes.py")
                
                subprocess.Popen([sys.executable, clipping_path, system_id])
                print(f"✓ Launched Clipping Planes Viewer for {system_id}")
                window.status_bar.config(text=f"✓ Clipping Planes Viewer ({system_id}) Launched")
            except Exception as e:
                print(f"Error launching clipping planes: {e}")
                window.status_bar.config(text=f"❌ Error: {str(e)}")
        
        # Launch Curved MPR viewer
        elif action == "curved_mpr" and system_id:
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                curved_mpr_path = os.path.join(current_dir, "curvedMPR.py")
                
                subprocess.Popen([sys.executable, curved_mpr_path, system_id])
                print(f"✓ Launched Curved MPR Viewer for {system_id}")
                window.status_bar.config(text=f"✓ Curved MPR Viewer ({system_id}) Launched")
            except Exception as e:
                print(f"Error launching Curved MPR viewer: {e}")
                window.status_bar.config(text=f"❌ Error: {str(e)}")

# Create main window
root = tk.Tk()
app = MedicalSystemsApp(root)
root.mainloop()