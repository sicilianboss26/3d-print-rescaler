import streamlit as st
import trimesh
import io
import math

def get_bounds(mesh):
    x, y, z = mesh.extents[0], mesh.extents[1], mesh.extents[2]
    metrics = {"Width (X)": x, "Depth (Y)": y, "Height (Z)": z}
    
    # If X and Y are nearly identical (within 1mm), it's a round circular part!
    if abs(x - y) < 1.0:
        metrics["🔴 Diameter"] = (x + y) / 2.0
        
    return metrics

st.set_page_config(page_title="3D Print Rescaler", layout="centered")
st.title("🖨️ Hay Feeder Round-Part Dimension Calculator")

uploaded_files = st.file_uploader("Upload STL files", type=["stl"], accept_multiple_files=True)

if uploaded_files:
    pct = st.number_input("Scale %", min_value=1.0, max_value=1000.0, value=100.0, step=5.0)
    factor = pct / 100.0
    
    st.write(f"### ⚡ Live Dimensions ({pct}% / {factor:.4f}x)")
    
    for f in uploaded_files:
        try:
            mesh = trimesh.load(io.BytesIO(f.getvalue()), file_type='stl')
            
            orig = get_bounds(mesh)
            if factor != 1.0:
                mesh.apply_scale(factor)
            new_dims = get_bounds(mesh)
            
            with st.expander(f"📦 {f.name}", expanded=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Original Size**")
                    for k, v in orig.items():
                        if "Diameter" in k:
                            st.markdown(f"🎯 **{k}: {v:.1f} mm ({v/25.4:.2f} in)**")
                        else:
                            st.caption(f"{k}: {v:.1f} mm ({v/25.4:.2f} in)")
                with c2:
                    st.markdown("**Scaled New Size**")
                    for k, v in new_dims.items():
                        if "Diameter" in k:
                            st.markdown(f"🔥 **{k}: {v:.1f} mm ({v/25.4:.2f} in)**")
                        else:
                            st.caption(f"**{k}: {v:.1f} mm ({v/25.4:.2f} in)**")
            
                buf = mesh.export(file_type='stl')
                st.download_button(label=f"💾 Download Scaled {f.name}", data=buf, file_name=f"{f.name.rsplit('.', 1)[0]}_scaled.stl", mime="application/sla", key=f"dl_{f.name}")
        except Exception as e:
            st.error(f"Error {f.name}: {e}")
