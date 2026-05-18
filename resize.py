import streamlit as st
import trimesh
import io

def get_bounds(mesh):
    return {"X (Width)": mesh.extents[0], "Y (Depth)": mesh.extents[1], "Z (Height)": mesh.extents[2]}

st.set_page_config(page_title="3D Print Rescaler", layout="centered")
st.title("🖨️ Multi-Part 3D Rescaler & Fit Preview")

uploaded_files = st.file_uploader("Upload STL files", type=["stl"], accept_multiple_files=True)

if uploaded_files:
    pct = st.number_input("Scale %", min_value=1.0, max_value=1000.0, value=100.0, step=5.0)
    factor = pct / 100.0
    
    scene = trimesh.Scene()
    st.write(f"### ⚡ Live Preview ({pct}% / {factor:.4f}x)")
    
    for f in uploaded_files:
        try:
            mesh = trimesh.load(io.BytesIO(f.getvalue()), file_type='stl')
            orig = get_bounds(mesh)
            
            if factor != 1.0:
                mesh.apply_scale(factor)
            new_dims = get_bounds(mesh)
            
            # Add to our visual scene assembly
            scene.add_geometry(mesh)
            
            with st.expander(f"📦 {f.name}", expanded=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Original Size**")
                    for k, v in orig.items():
                        st.caption(f"{k}: {v:.1f}mm ({v/25.4:.2f}in)")
                with c2:
                    st.markdown("**New Size**")
                    for k, v in new_dims.items():
                        st.caption(f"**{k}: {v:.1f}mm ({v/25.4:.2f}in)**")
            
                buf = mesh.export(file_type='stl')
                st.download_button(label=f"💾 Download {f.name}", data
