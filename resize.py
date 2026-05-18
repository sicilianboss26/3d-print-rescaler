import streamlit as st
import trimesh
import io
import base64

def get_bounds(mesh):
    return {"Width (X)": mesh.extents[0], "Depth (Y)": mesh.extents[1], "Height (Z)": mesh.extents[2]}

st.set_page_config(page_title="3D Print Rescaler", layout="centered")
st.title("🖨️ Multi-Part Rescaler & Joint Alignment")

uploaded_files = st.file_uploader("Upload STL files", type=["stl"], accept_multiple_files=True)

if uploaded_files:
    pct = st.number_input("Scale %", min_value=1.0, max_value=1000.0, value=100.0, step=5.0)
    factor = pct / 100.0
    
    st.write(f"### ⚡ Live Metrics ({pct}% / {factor:.4f}x)")
    
    processed_parts = {}
    file_name_map = {}
    colors = ["#FF5733", "#33FF57", "#3357FF", "#F3FF33", "#FF33F3", "#33FFF0"]
    
    for i, f in enumerate(uploaded_files):
        try:
            mesh = trimesh.load(io.BytesIO(f.getvalue()), file_type='stl')
            
            # 1. Bring everything to a shared starting baseline so they aren't lost in space
            mesh.apply_translation(-mesh.centroid)
            
            orig = get_bounds(mesh)
            if factor != 1.0:
                mesh.apply_scale(factor)
            new_dims = get_bounds(mesh)
            
            processed_parts[f.name] = mesh
            file_name_map[f.name] = i
            
            with st.expander(f"📦 {f.name}", expanded=False):
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
                st.download_button(label=f"💾 Download {f.name}", data=buf, file_name=f"{f.name.rsplit('.', 1)[0]}_scaled.stl", mime="application/sla", key=f"dl_{f.name}")
        except Exception as e:
            st.error(f"Error {f.name}: {e}")

    if processed_parts:
        st.write("---")
        st.write("### 🤝 Select Parts to Align")
        selected_names = st.multiselect(
            "Choose files to put on the table:",
            options=list(processed_parts.keys()),
            default=list(processed_parts.keys())[:2]
        )
        
        if selected_names:
            try:
                scene = trimesh.Scene()
                active_indices = []
                
                st.sidebar.header("🕹️ Joint Alignment Sliders")
                st.sidebar.caption("Manually slide the parts into position to check clearances:")
                
                for name in selected_names:
                    idx = file_name_map[name]
                    active_indices.append(idx)
                    
                    # Create a copy so shifting around doesn't alter the original download file
                    temp_mesh = processed_parts[name].copy()
                    
                    # Add dedicated fine-tuning movement sliders for this specific part in the sidebar
                    st.sidebar.markdown(f"**📍 Adjust: {name}**")
                    x_adj = st.sidebar.slider(f"Move X", -150.0, 150.0, 0.0, step=0.5, key=f"x_slide_{idx}")
                    y_adj = st.sidebar.slider(f"Move Y", -150.0, 150.0, 0.0, step=0.5, key=f"y_slide_{idx}")
                    z_adj = st.sidebar.slider(f"Move Z", -150.0, 150.0, 0.0, step=0.5, key=f"z_slide_{idx}")
                    
                    # Slide it into its actual placement position
                    temp_mesh.apply_translation([x_adj, y_adj, z_adj])
                    scene.add_geometry(temp_mesh, node_name=f"part_{idx}")
                
                st.write(f"### 🔍 Live 3D Fit Assembly Preview")
                
                glb_data = scene.export(file_type='glb')
                encoded = base64.b64encode(glb_data).decode()
                
                color_scripts = ""
                for display_order, mesh_idx in enumerate(active_indices):
                    pick_color = colors[mesh_idx % len(colors)]
                    color_scripts += f"""
                    const mat_{display_order} = modelViewer.model.materials[{display_order}];
                    if (mat_{display_order}) {{
                        mat_{display_order}.pbrMetallicRoughness.setBaseColorFactor("{pick_color}");
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
