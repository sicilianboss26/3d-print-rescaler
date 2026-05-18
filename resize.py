import streamlit as st
import trimesh
import io

def get_bounds(mesh):
    """Calculate the dimensions of the mesh bounding box."""
    size_x, size_y, size_z = mesh.extents
    dims = {
        "X (Width)": size_x,
        "Y (Depth)": size_y,
        "Z (Height)": size_z
    }
    return dims

st.set_page_config(page_title="3D Print Rescaler", layout="centered")
st.title("🖨️ 3D Print STL Rescaler")
st.write("Upload an STL file, adjust the scale, and download the modified version.")

uploaded_file = st.file_uploader("Choose an STL file", type=["stl"])

if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.getvalue()
        file_stream = io.BytesIO(file_bytes)
        mesh = trimesh.load(file_stream, file_type='stl')
        
        orig_dims = get_bounds(mesh)
        
        st.subheader("Original Dimensions (mm)")
        cols = st.columns(3)
        for i, (axis, val) in enumerate(orig_dims.items()):
            cols[i].metric(axis, f"{val:.2f}")
            
        st.sidebar.header("Scaling Options")
        scale_type = st.sidebar.radio("Scale by:", ["Percentage", "Target Dimensions"])
        
        scale_factor = 1.0
        
        if scale_type == "Percentage":
            percentage = st.sidebar.number_input("Scale %", min_value=1.0, max_value=1000.0, value=100.0, step=5.0)
            scale_factor = percentage / 100.0
        else:
            target_axis = st.sidebar.selectbox("Match target size to:", list(orig_dims.keys()))
            target_size = st.sidebar.number_input("Target Size (mm)", min_value=0.1, value=float(orig_dims[target_axis]))
            scale_factor = target_size / orig_dims[target_axis]
            st.sidebar.caption(f"Calculated uniform scale factor: **{scale_factor:.4f}x**")

        if scale_factor != 1.0:
            mesh.apply_scale(scale_factor)
            
            new_dims = get_bounds(mesh)
            st.subheader("Rescaled Dimensions (mm)")
            cols_new = st.columns(3)
            for i, (axis, val) in enumerate(new_dims.items()):
                cols_new[i].metric(axis, f"{val:.2f}", delta=f"{val - orig_dims[axis]:.2f}")

        export_bytes = mesh.export(file_type='stl')
        
        orig_name = uploaded_file.name.rsplit('.', 1)[0]
        new_filename = f"{orig_name}_rescaled_{scale_factor:.2f}.stl"
        
        st.write("---")
        st.download_button(
            label="💾 Download Rescaled STL",
            data=export_bytes,
            file_name=new_filename,
            mime="application/sla",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error processing STL file: {e}")
