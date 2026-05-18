import streamlit as st
import trimesh
import io
import base64
import numpy as np

def get_bounds(mesh):
    return {"Width (X)": mesh.extents[0], "Depth (Y)": mesh.extents[1], "Height (Z)": mesh.extents[2]}

st.set_page_config(page_title="3D Print Rescaler", layout="centered")
st.title("🖨️ Mobile-Touch Fit Previewer")

uploaded_files = st.file_uploader("Upload STL files", type=["stl"], accept_multiple_files=True)

if uploaded_files:
    # Initialize session tracking for translations and rotations so clicks persist
    if "offsets" not in st.session_state:
        st.session_state.offsets = {}
    
    pct = st.number_input("Scale %", min_value=1.0, max_value=1000.0, value=100.0, step=5.0)
    factor = pct / 100.0
    
    processed_parts = {}
    file_name_map = {}
    colors = ["#FF5733", "#33FF57", "#3357FF", "#F3FF33", "#FF33F3", "#33FFF0"]
    
    for i, f in enumerate(uploaded_files):
        try:
            # Setup stable tracking keys for each file
            if f.name not in st.session_state.offsets:
                st.session_state.offsets[f.name] = {
                    "x": 0.0, "y": 0.0, "z": 0.0,
                    "roll": 0.0, "tumble": 0.0, "spin": 0.0
                }
                
            mesh = trimesh.load(io.BytesIO(f.getvalue()), file_type='stl')
            mesh.apply_translation(-mesh.centroid)  # Center baseline
            
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
        st.write("### 🤝 Target Match Assembly")
        
        selected_names = st.multiselect(
            "Select parts to match up on the table:",
            options=list(processed_parts.keys()),
            default=list(processed_parts.keys())[:2]
        )
        
        if selected_names:
            st.write("### 🕹️ Quick Touch Alignment Menu")
            st.caption("Tap a part name to open its quick rotation and nudge buttons:")
            
            # Create a clean tab menu for editing positions cleanly on a phone layout
            part_tabs = st.tabs([f"📍 {name}" for name in selected_names])
            
            for idx, name in enumerate(selected_names):
                with part_tabs[idx]:
                    state = st.session_state.offsets[name]
                    
                    # 180 Degree Quick Flips
                    st.markdown("**Quick 180° Flips (Fix Backwards Parts):**")
                    cb1, cb2, cb3 = st.columns(3)
                    with cb1:
                        if st.button("Flip X (180°)", key=f"fx_{name}"):
                            state["roll"] = (state["roll"] + 180) % 360
                            st.rerun()
                    with cb2:
                        if st.button("Flip Y (180°)", key=f"fy_{name}"):
                            state["tumble"] = (state["tumble"] + 180) % 360
                            st.rerun()
                    with cb3:
                        if st.button("Flip Z (180°)", key=f"fz_{name}"):
                            state["spin"] = (state["spin"] + 180) % 360
                            st.rerun()
                            
                    # 90 Degree Rotation Adjustments
                    st.markdown("**Rotate 90° Steps:**")
                    r1, r2, r3 = st.columns(3)
                    with r1:
                        if st.button("🔄 Roll +90°", key=f"r90_{name}"):
                            state["roll"] = (state["roll"] + 90) % 360
                            st.rerun()
                    with r2:
                        if st.button("🔄 Tumble +90°", key=f"t90_{name}"):
                            state["tumble"] = (state["tumble"] + 90) % 360
                            st.rerun()
                    with r3:
                        if st.button("🔄 Spin +90°", key=f"s90_{name}"):
                            state["spin"] = (state["spin"] + 90) % 360
                            st.rerun()

                    # Precise Nudge/Position Buttons
                    st.markdown("**Position Nudge Buttons (mm):**")
                    n1, n2, n3, n4 = st.columns(4)
                    with n1:
                        if st.button("⬅️ X -10", key=f"xm_{name}"):
                            state["x"] -= 10.0
                            st.rerun()
                    with n2:
                        if st.button("➡️ X +10", key=f"xp_{name}"):
                            state["x"] += 10.0
                            st.rerun()
                    with n3:
                        if st.button("⬇️ Z -10", key=f"zm_{name}"):
                            state["z"] -= 10.0
                            st.rerun()
                    with n4:
                        if st.button("⬆️ Z +10", key=f"zp_{name}"):
                            state["z"] += 10.0
                            st.rerun()

                    if st.button("🎯 Reset to Center", key=f"rst_{name}"):
                        st.session_state.offsets[name] = {"x":0.0, "y":0.0, "z":0.0, "roll":0.0, "tumble":0.0, "spin":0.0}
                        st.rerun()

            # Compile Scene using stored Touch state variables
            try:
                scene = trimesh.Scene()
                active_indices = []
                
                for name in selected_names:
                    mesh_idx = file_name_map[name]
                    active_indices.append(mesh_idx)
                    
                    temp_mesh = processed_parts[name].copy()
                    state = st.session_state.offsets[name]
                    
                    # Apply Rotation Matricies calculated from your button taps
                    if state["roll"] != 0:
                        temp_mesh.apply_transform(trimesh.transformations.rotation_matrix(np.radians(state["roll"]), [1, 0, 0]))
                    if state["tumble"] != 0:
                        temp_mesh.apply_transform(trimesh.transformations.rotation_matrix(np.radians(state["tumble"]), [0, 1, 0]))
                    if state["spin"] != 0:
                        temp_mesh.apply_transform(trimesh.transformations.rotation_matrix(np.radians(state["spin"]), [0, 0, 1]))
                        
                    # Apply Nudge Translation Values
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
