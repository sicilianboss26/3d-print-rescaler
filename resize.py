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
st.title("🖨️ Multi-Part 3D Print STL Rescaler")
st.write("Upload one or multiple STL files, adjust the uniform scale, and download the modified versions.")

# Changed to accept multiple files
uploaded_files = st.file_uploader("Choose STL files", type=["stl"], accept_multiple_files=True)

if uploaded_files:
    st.sidebar.header("Global Scaling Options")
    scale_type = st.sidebar.radio("Scale by:", ["Percentage", "Target Dimensions (First File Only)"])
    
    scale_factor = 1.0
    first_mesh = None
    first_orig_dims = None
    
    # Process the first file just to calculate the scaling factors if using target dimensions
    try:
        first_file_bytes = uploaded_files[0].getvalue()
        first_mesh = trimesh.load(io.BytesIO(first_file_bytes), file_type='stl')
        first_orig_dims = get_bounds(first_mesh)
    except Exception as e:
        st.error(f"Error reading the first file for scaling setup: {e}")

    if first_orig_dims:
        if scale_type == "Percentage":
            percentage = st.sidebar.number_input("Scale %", min_value=1.0, max_value=1000.0, value=100.0, step=5.0)
            scale_factor = percentage / 100.0
        else:
            st.sidebar.caption("Define the target size based on your first uploaded file. All other files will scale by the exact same ratio.")
            target_axis = st.sidebar.selectbox("Match target size to:", list(first_orig_dims.keys()))
            target_size = st.sidebar.number_input("Target Size (mm)", min_value=0.1, value=float(first_orig_dims[target_axis]))
            scale_factor = target_size / first_orig_dims[target_axis]
            st.sidebar.caption(f"Calculated uniform scale factor: **{scale_factor:.4f}x**")

        st.success(f"Applying a **{scale_factor:.4f}x** scale across all {len(uploaded_files)} files.")
        st.write("---")

        # Loop through every uploaded file and process them
        for uploaded_file in uploaded_files:
            try:
                file_bytes = uploaded_file.getvalue()
                mesh = trimesh.load(io.BytesIO(file_bytes), file_type='stl')
                orig_dims = get_bounds(mesh)
                
                with st.expander(f"📦 {uploaded_file.name}", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Original Size:**")
                        for axis, val in orig_dims.items():
                            st.caption(f"{axis}: {val:.2f} mm")
                    
                    if scale_factor != 1.0:
                        mesh.apply_scale(scale_factor)
                    
                    new_dims = get_bounds(mesh)
                    
                    with col2:
                        st.markdown("**New Size:**")
                        for axis, val in new_dims.items():
                            st.caption(f"{axis}: {val:.2f} mm")
                    
                    export_bytes = mesh.export(file_type='stl')
                    orig_name = uploaded_file.name.rsplit('.', 1)[0]
                    new_filename = f"{orig_name}_rescaled_{scale_factor:.2f}.stl"
                    
                    st.download_button(
                        label=f"💾 Download {new_filename}",
                        data=export_bytes,
                        file_name=new_filename,
                        mime="application/sla",
                        key=f"dl_{uploaded_file.name}"
                    )
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
