import os
import numpy as np
from typing import Tuple, Optional, Dict, Any
import json
import trimesh
import tempfile
import subprocess

class ModelImporter:
    """Import 3D models from various formats for CG visualization"""
    
    @staticmethod
    def import_stl(file_path: str) -> Optional[trimesh.Trimesh]:
        """Import an STL file"""
        try:
            mesh = trimesh.load(file_path)
            return mesh
        except Exception as e:
            print(f"Error importing STL file: {e}")
            return None
    
    @staticmethod
    def import_obj(file_path: str) -> Optional[trimesh.Trimesh]:
        """Import an OBJ file"""
        try:
            mesh = trimesh.load(file_path)
            return mesh
        except Exception as e:
            print(f"Error importing OBJ file: {e}")
            return None
    
    @staticmethod
    def import_step(file_path: str) -> Optional[trimesh.Trimesh]:
        """Import a STEP file (requires FreeCAD)"""
        try:
            # Create a temporary directory for conversion
            with tempfile.TemporaryDirectory() as temp_dir:
                output_file = os.path.join(temp_dir, "converted.stl")
                
                # Use FreeCAD to convert STEP to STL
                # Note: This requires FreeCAD to be installed
                conversion_script = f"""
                import FreeCAD
                import Part
                import Mesh
                
                doc = FreeCAD.newDocument()
                shape = Part.Shape()
                shape.read("{file_path}")
                doc.addObject("Part::Feature", "Part").Shape = shape
                Mesh.export([doc.Part], "{output_file}")
                """
                
                script_path = os.path.join(temp_dir, "convert.py")
                with open(script_path, 'w') as f:
                    f.write(conversion_script)
                
                # Run FreeCAD with the conversion script
                subprocess.run(["freecad", "-c", script_path], check=True)
                
                # Load the converted STL file
                if os.path.exists(output_file):
                    mesh = trimesh.load(output_file)
                    return mesh
                else:
                    print("Conversion failed: output file not found")
                    return None
        except Exception as e:
            print(f"Error importing STEP file: {e}")
            return None
    
    @staticmethod
    def import_fusion360(file_path: str) -> Optional[trimesh.Trimesh]:
        """Import a Fusion 360 file (f3d)"""
        # Fusion 360 files need to be exported to a format like STL first
        # This is typically done through the Fusion 360 UI
        print("Fusion 360 files must be exported to STL, OBJ, or STEP format first")
        return None
    
    @staticmethod
    def import_openvsp(file_path: str) -> Optional[trimesh.Trimesh]:
        """Import an OpenVSP file"""
        # OpenVSP files need to be exported to a format like STL first
        # This is typically done through the OpenVSP UI
        print("OpenVSP files must be exported to STL or OBJ format first")
        return None
    
    @classmethod
    def import_model(cls, file_path: str) -> Optional[trimesh.Trimesh]:
        """Import a 3D model based on file extension"""
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
            
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.stl':
            return cls.import_stl(file_path)
        elif file_ext == '.obj':
            return cls.import_obj(file_path)
        elif file_ext == '.step' or file_ext == '.stp':
            return cls.import_step(file_path)
        elif file_ext == '.f3d':
            return cls.import_fusion360(file_path)
        elif file_ext == '.vsp':
            return cls.import_openvsp(file_path)
        else:
            print(f"Unsupported file format: {file_ext}")
            return None
    
    @staticmethod
    def get_model_dimensions(mesh: trimesh.Trimesh) -> Tuple[float, float, float]:
        """Get the dimensions of a 3D model"""
        if mesh is None:
            return (0, 0, 0)
            
        extents = mesh.bounding_box.extents
        return tuple(extents)
    
    @staticmethod
    def get_model_center(mesh: trimesh.Trimesh) -> Tuple[float, float, float]:
        """Get the center of a 3D model"""
        if mesh is None:
            return (0, 0, 0)
            
        center = mesh.bounding_box.center
        return tuple(center) 