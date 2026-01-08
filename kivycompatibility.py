import os
import platform

def get_opengl_version():
    try:
        from OpenGL import GL
        from OpenGL.GL import glGetString, GL_VERSION
        return glGetString(GL_VERSION).decode()
    except Exception as e:
        return "0.0"  # Fallback if OpenGL not found

def parse_version(version_str):
    parts = version_str.split(".")
    major = int(parts[0]) if parts else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    return major + minor / 10

# OS check
system = platform.system()
if system == "Windows":
    version_str = get_opengl_version()
    version = parse_version(version_str)
    
    print(f"[🔍] Detected OpenGL version: {version_str}")
    if version < 2.0:
        print("[⚠️] OpenGL < 2.0 detected — switching to angle_sdl2 backend")
        os.environ["KIVY_GL_BACKEND"] = "angle_sdl2"
    else:
        print("[✅] OpenGL version is sufficient")