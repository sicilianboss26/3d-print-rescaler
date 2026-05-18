import streamlit as st
import trimesh
import io
import base64

def get_bounds(mesh):
    return {"Width (X)": mesh.extents[0], "Depth (Y)": mesh.extents[1], "Height (Z)": mesh.extents[2]}

st.set_page_config(page_title="3D Print Rescaler", layout="centered")
st.title("🖨️ Multi-Part Rescaler & Fit Preview")

uploaded_files = st.file_uploader("Upload STL files", type=["stl"], accept_multiple_files=True)

if uploaded_files:
    pct = st.number_input("Scale %", min_value=1.0, max_value=1000.0, value=100.0, step=5.0)
    factor = pct / 100.0
    
    scene = trimesh.Scene()
    st.write(f"### ⚡ Live Metrics ({pct}% / {factor:.4f}x)")
    
    for f in uploaded_files:
        try:
            mesh = trimesh.load(io.BytesIO(f.getvalue()), file_type='stl')
            orig = get_bounds(mesh)
            
            if factor != 1.0:
                mesh.apply_scale(factor)
            new_dims = get_bounds(mesh)
            
            scene.add_geometry(mesh)
            
            with st.expander(f"📦 {f.name}", expanded=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Original Size**")
                    for k, v in orig.items():
                        st.caption(f"{k}: {v:.1f} mm ({v/25.4:.2f} in)")
                with c2:
                    st.markdown("**New Size**")
                    for k, v in new_dims.items():
                        st.caption(f"**{k}: {v:.1f} mm ({v/25.4:.2f} in)**")
            
                buf = mesh.export(file_type='stl')
                dl_label = f"💾 Download {f.name}"
                out_name = f"{f.name.rsplit('.', 1)[0]}_scaled.stl"
                st.download_button(label=dl_label, data=buf, file_name=out_name, mime="application/sla", key=f"dl_{f.name}")
        except Exception as e:
            st.error(f"Error {f.name}: {e}")

    if len(uploaded_files) > 0:
        try:
            st.write("### 🔍 Live 3D Fit Assembly Preview")
            # Export assembly scene as an embedded web GLTF data stream
            gltf_data = scene.export(file_type='gltf')
            encoded = base64.b64encode(gltf_data).decode()
            
            # Use a robust, universal HTML5 canvas deployment to view the model
            html_string = f"""
            <script type=module src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script>
            <model-viewer src="data:model/gltf+json;base64,{encoded}" ar camera-controls touch-action="none" style="width: 100%; height: 500px; background-color: #f0f2f6; border-radius: 10px;"></model-viewer>
            """
            st.components.v1.html(html_string, height=510, scrolling=False)
        except Exception as scene_err:
            st.error(f"Assembly render error: {scene_err}")
