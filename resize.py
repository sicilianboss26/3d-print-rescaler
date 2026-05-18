import streamlit as st
import trimesh
import io
import base64
import numpy as np

def get_bounds(mesh):
    return {"Width (X)": mesh.extents[0], "Depth (Y)": mesh.extents[1], "Height (Z)": mesh.extents[2]}

st.set_page_config(page_title="3D Print Rescaler", layout="centered")
st.title("🖨️ 3D Print Alignment Studio")

uploaded_files = st.file_uploader("Upload STL files", type=["stl"], accept_multiple_files=True)

if uploaded_files:
    if "offsets" not in st.session_state:
        st.session_state.offsets = {}
    
    pct = st.number_input("Scale %", min_value=1.0, max_value=1000.0, value=100.0, step=5.0)
    factor = pct / 100.0
    
    processed_parts = {}
    file_name_map = {}
    colors = ["#FF5733", "#33FF57", "#3357FF", "#F3FF33", "#FF33F3", "#33FFF0"]
    
    for i, f in enumerate(uploaded_files):
        try:
            if f.name not in st.session_state.offsets:
                st.session_state.offsets[f.name] = {
                    "x": 0.0, "y": 0.0, "z": 0.0, "roll": 0.0, "tumble": 0.0, "spin": 0.0
                }
                
            mesh = trimesh.load(io.BytesIO(f.getvalue()), file_type='stl')
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
                    st.markdown("**Original**")
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
        
        # Main table selector
        selected_names = st.multiselect(
            "Select parts to display on the assembly table:",
            options=list(processed_parts.keys()),
            default=list(processed_parts.keys())[:2]
        )
        
        if selected_names:
            # --- CONSOLIDATED SIDEBAR COMPONENT PANEL ---
            st.sidebar.header("🛠️ Part Transform Panel")
            target_part = st.sidebar.selectbox("Select active part to adjust:", options=selected_names)
            
            if target_part:
                state = st.session_state.offsets[target_part]
                st.sidebar.markdown(f"**Modifying:** `{target_part}`")
                
                # 180 Flips
                st.sidebar.markdown("**Quick 180° Flips:**")
                fx, fy, fz = st.sidebar.columns(3)
                if fx.button("Flip X", key="side_fx"):
                    state["roll"] = (state["roll"] + 180) % 360
                    st.rerun()
                if fy.button("Flip Y", key="side_fy"):
                    state["tumble"] = (state["tumble"] + 180) % 360
                    st.rerun()
                if fz.button("Flip Z", key="side_fz"):
                    state["spin"] = (state["spin"] + 180) % 360
                    st.rerun()
                
                # Nudge steps
                st.sidebar.markdown("**Nudge Position (mm):**")
                nx1, nx2 = st.sidebar.columns(2)
                if nx1.button("⬅️ X -10", key="side_xm"): state["x"] -= 10.0; st.rerun()
                if nx2.button("➡️ X +10", key="side_xp"): state["x"] += 10.0; st.rerun()
                
                nz1, nz2 = st.sidebar.columns(2)
                if nz1.button("⬇️ Z -10", key="side_zm"): state["z"] -= 10.0; st.rerun()
                if nz2.button("⬆️ Z +10", key="side_zp"): state["z"] += 10.0; st.rerun()
                
                if st.sidebar.button("🎯 Reset Part to Center", key="side_rst"):
                    st.session_state.offsets[target_part] = {"x":0.0, "y":0.0, "z":0.0, "roll":0.0, "tumble":0.0, "spin":0.0}
                    st.rerun()

            # Compile Scene
            try:
                scene = trimesh.Scene()
                active_indices = []
                
                for name in selected_names:
                    mesh_idx = file_name_map[name]
                    active_indices.append(mesh_idx)
                    
                    temp_mesh = processed_parts[name].copy()
                    state = st.session_state.offsets[name]
                    
                    if state["roll"] != 0:
                        temp_mesh.apply_transform(trimesh.transformations.rotation_matrix(np.radians(state["roll"]), [1, 0, 0]))
                    if state["tumble"] != 0:
                        temp_mesh.apply_transform(trimesh.transformations.rotation_matrix(np.radians(state["tumble"]), [0, 1, 0]))
                    if state["spin"] != 0:
                        temp_mesh.apply_transform(trimesh.transformations.rotation_matrix(np.radians(state["spin"]), [0, 0, 1]))
                        
                    temp_mesh.apply_translation([state["x"], state["y"], state["z"]])
                    scene.add_geometry(temp_mesh, node_name=f"part_{mesh_idx}")
                
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
