import streamlit as st
import trimesh
import io
import base64

def get_bounds(mesh):
    return {"Width (X)": mesh.extents[0], "Depth (Y)": mesh.extents[1], "Height (Z)": mesh.extents[2]}

st.set_page_config(page_title="3D Print Rescaler", layout="centered")
st.title("🖨️ Multi-Part Rescaler & Auto-Fit Preview")

uploaded_files = st.file_uploader("Upload STL files", type=["stl"], accept_multiple_files=True)

if uploaded_files:
    pct = st.number_input("Scale %", min_value=1.0, max_value=1000.0, value=100.0, step=5.0)
    factor = pct / 100.0
    
    scene = trimesh.Scene()
    st.write(f"### ⚡ Live Metrics ({pct}% / {factor:.4f}x)")
    
    # Pre-defined bright, high-contrast hex colors for the viewer canvas
    colors = ["#FF5733", "#33FF57", "#3357FF", "#F3FF33", "#FF33F3", "#33FFF0"]
    
    for i, f in enumerate(uploaded_files):
        try:
            mesh = trimesh.load(io.BytesIO(f.getvalue()), file_type='stl')
            
            # AUTOMATIC JOIN: Force the center of mass/bounds to (0,0,0) so they automatically align
            mesh.visual.face_colors = [255, 255, 255, 255] # Reset default
            mesh.apply_translation(-mesh.centroid)
            
            orig = get_bounds(mesh)
            
            if factor != 1.0:
                mesh.apply_scale(factor)
            new_dims = get_bounds(mesh)
            
            # Add to scene geometry
            scene.add_geometry(mesh, node_name=f"part_{i}")
            
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
            st.write("### 🔍 Live 3D Fit Assembly Preview (Centered)")
            glb_data = scene.export(file_type='glb')
            encoded = base64.b64encode(glb_data).decode()
            
            # Build script inject to force the custom colors onto each unique mesh node inside model-viewer
            color_scripts = ""
            for i in range(len(uploaded_files)):
                pick_color = colors[i % len(colors)]
                color_scripts += f"""
                const material_{i} = modelViewer.model.materials[{i}];
                if (material_{i}) {{
                    material_{i}.pbrMetallicRoughness.setBaseColorFactor("{pick_color}");
                }}
                """

            html_string = f"""
            <script type=module src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js"></script>
            <model-viewer id="fit-viewer" src="data:model/gltf-binary;base64,{encoded}" ar camera-controls touch-action="none" style="width: 100%; height: 500px; background-color: #1e1e24; border-radius: 10px;"></model-viewer>
            
            <script>
            const modelViewer = document.querySelector("#fit-viewer");
            modelViewer.addEventListener("load", () => {{
                {color_scripts}
            }});
            </script>
            """
            st.components.v1.html(html_string, height=510, scrolling=False)
        except Exception as scene_err:
            st.error(f"Assembly render error: {scene_err}")
