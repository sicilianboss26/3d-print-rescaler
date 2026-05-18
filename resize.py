import streamlit as st
import trimesh
import io

def get_bounds(mesh):
    """Calculate the dimensions of the mesh bounding box."""
    size_x, size_y, size_z = mesh.extents
    dims = {"X (Width)": size_x, "Y (Depth)": size_y, "Z (Height)": size_z}
    return dims

st.set_page_config(page_title="3D Print Rescaler", layout="centered")
st.title("🖨️ Multi-Part 3D Print STL Rescaler")
st.write("Upload your STL files, adjust the scale, and watch the dimensions update instantly.")

uploaded_files = st.file_uploader("Choose STL files", type=["stl"], accept_multiple_files=True)

if uploaded_files:
    st.sidebar.header("⚖️ Live Scaling Controller")
    scale_type = st.sidebar.radio("Scale Method:", ["Percentage", "Target Dimensions (First File)"])
    
    scale_factor = 1.0
    first_orig_dims = None
    
    # Pre-load first file to establish base metrics
    try:
        first_mesh = trimesh.load(io.BytesIO(uploaded_files[0].getvalue()), file_type='stl')
        first_orig_dims = get_bounds(first_mesh)
    except Exception as e:
        st.error(f"Error loading calibration file: {e}")

    if first_orig_dims:
        if scale_type == "Percentage":
            percentage = st.sidebar.number_input("Scale %", min_value=1.0, max_value=1000.0, value=100.0, step=5.0)
            scale_factor = percentage / 100.0
        else:
            target_axis = st.sidebar.selectbox("Match target size to:", list(first_orig_dims.keys()))
            target_size = st.sidebar.number_input("Target Size (mm)", min_value=0.1, value=float(first_orig_dims[target_axis]))
            scale_factor = target_size / first_orig_dims[target_axis]

        # --- LIVE SCALING LIVE PREVIEW VISUAL ---
        st.sidebar.write("---")
        st.sidebar.subheader("📊 Live Scaling Factors")
        st.sidebar.metric(label="Multiplier", value
