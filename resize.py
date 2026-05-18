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
        
        selected_names = st.multiselect(
            "Select parts to display on the assembly table:",
            options=list(processed_parts.keys()),
            default=list(processed_parts.keys())[:2]
        )
        
        if selected_names:
            # --- SIDEBAR PRECISION PANEL ---
            st.sidebar.header("🛠️ Precision Transform Panel")
            target_part = st.sidebar.selectbox("Select active part to adjust:", options=selected_names)
            
            if target_part:
                state = st.session_state.offsets[target_part]
                st.sidebar.markdown(f"**Modifying:** `{target_part}`")
                
                # --- POSITION (XYZ) CONTROL ---
                st.sidebar.markdown("### 📍 Position Offset (mm)")
                state["x"] = st.sidebar.number_input("Position X", value=state["x"], step=1.0, key=f"num_x_{target_part}")
                st.sidebar.slider("Slide X", -200.0, 200.0, float(state["x"]), step=0.5, key=f"sld_x_{target_part}", label_visibility="collapsed")
                
                state["y"] = st.sidebar.number_input("Position Y", value=state["y"], step=1.0, key=f"num_y_{target_part}")
                st.sidebar.slider("Slide Y", -200.0, 200.0, float(state["y"]), step=0.5, key=f"sld_y_{target_part}", label_visibility="collapsed")
                
                state["z"] = st.sidebar.number_input("Position Z", value=state["z"], step=1.0, key=f"num_z_{target_part}")
                st.sidebar.slider("Slide Z", -200.0, 200.0, float(state["z"]), step=0.5, key=f"sld_z_{target_part}", label_visibility="collapsed")
                
                # --- ROTATION CONTROL ---
                st.sidebar.markdown("### 🔄 Rotation (Degrees)")
                state["roll"] = st.sidebar.number_input("Roll (X Axis)", value=state["roll"], step=5.0, key=f"num_roll_{target_part}")
                st.sidebar.slider("Slide Roll", 0.0, 360.0, float(state["roll"]), step=1.0, key=f"sld_roll_{target_part}", label_visibility="collapsed")
                
                state["tumble"] = st.sidebar.number_input("Tumble (Y Axis)", value=state["tumble"], step=5.0, key=f"num_tumble_{target_part}")
                st.sidebar.slider("Slide Tumble", 0.0, 360.0, float(state["tumble"]), step=1.0, key=f"sld_tumble_{target_part}", label_visibility="collapsed")
                
                state["spin"] = st.sidebar.number_input("Spin (Z Axis)", value=state["spin"], step=5.0, key=f"num_spin_{target_part}")
                st.sidebar.slider("Slide Spin", 0.0, 360.0, float(state["spin"]), step=1.0, key=f"sld_spin_{target_part}", label_visibility="collapsed")
                
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
                    
                    # Read values directly from the combined interactive states
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
