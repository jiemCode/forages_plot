import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import io

st.set_page_config(
    page_title="Corrélations géochimiques",
    layout="wide",
    page_icon=""
)

st.title("Corrélations géochimiques")
st.caption("Chargez un fichier Excel : 1ère colonne = Forage, colonnes suivantes = éléments chimiques.")

# Sidebar
with st.sidebar:
    st.header("Données")
    uploaded = st.file_uploader("Fichier Excel (.xlsx)", type=["xlsx", "xls"])

    if uploaded:
        sheet_names = pd.ExcelFile(uploaded).sheet_names
        sheet = st.selectbox("Feuille", sheet_names)
        df_raw = pd.read_excel(uploaded, sheet_name=sheet)

        label_col = df_raw.columns[0]
        df = df_raw.set_index(label_col)
        numeric_cols = df.select_dtypes(include="number").columns.tolist()

        st.divider()
        st.header("🧪 Éléments")
        elem_x = st.radio("Axe X →", numeric_cols, index=0)
        elem_y = st.radio("Axe Y ↑", numeric_cols, index=min(1, len(numeric_cols)-1))

        st.divider()
        st.header("Options")
        cmap_choice  = st.selectbox("Palette couleur", ["viridis","plasma","coolwarm","RdYlGn","Blues","tab10"])
        point_size   = st.slider("Taille des points", 20, 200, 70, step=10)
        show_reg     = st.checkbox("Droite de régression", value=True)
        show_labels  = st.checkbox("Afficher les noms", value=True)
        show_r2      = st.checkbox("Afficher R²", value=True)

        # Filtre sur forages
        st.divider()
        st.header("Filtrer les forages")
        all_forages = df.index.tolist()
        selected = st.multiselect("Forages à afficher", all_forages, default=all_forages)

# Main area
if not uploaded:
    st.info("👈 Chargez un fichier Excel dans le panneau gauche pour commencer.")
    st.stop()

if elem_x == elem_y:
    st.warning("Sélectionnez deux éléments différents.")
    st.stop()

df_plot = df.loc[selected, [elem_x, elem_y]].dropna()

if df_plot.empty:
    st.error("Aucune donnée disponible pour cette sélection.")
    st.stop()

x = df_plot[elem_x].values
y = df_plot[elem_y].values
labels_plot = df_plot.index.tolist()

# Couleurs par index
cmap_obj = cm.get_cmap(cmap_choice)
norm     = plt.Normalize(0, max(len(x) - 1, 1))
colors   = [cmap_obj(norm(i)) for i in range(len(x))]

# Stats
corr  = float(np.corrcoef(x, y)[0, 1])
r2    = corr ** 2
n_pts = len(x)

# Métriques
col1, col2, col3, col4 = st.columns(4)
col1.metric("Forages affichés", n_pts)
col2.metric("r (Pearson)", f"{corr:.3f}")
col3.metric("R²", f"{r2:.3f}")
interp = "forte" if abs(corr) > 0.7 else ("modérée" if abs(corr) > 0.4 else "faible")
sign   = "positive" if corr >= 0 else "négative"
col4.metric("Corrélation", f"{interp} {sign}")

st.divider()

# Figure
fig, ax = plt.subplots(figsize=(8, 6))

sc = ax.scatter(x, y, c=colors, s=point_size, alpha=0.85,
                edgecolors="white", linewidths=0.5, zorder=3)

if show_reg and len(x) > 1:
    z     = np.polyfit(x, y, 1)
    p     = np.poly1d(z)
    xline = np.linspace(x.min(), x.max(), 200)
    label_reg = f"y = {z[0]:.3f}x + {z[1]:.3f}"
    if show_r2:
        label_reg += f"   R² = {r2:.3f}"
    ax.plot(xline, p(xline), color="#e74c3c", linewidth=1.5,
            linestyle="--", alpha=0.8, label=label_reg, zorder=2)
    ax.legend(fontsize=9, framealpha=0.7)

if show_labels:
    for xi, yi, lbl in zip(x, y, labels_plot):
        ax.annotate(lbl, (xi, yi), fontsize=7, color="#555",
                    xytext=(4, 4), textcoords="offset points")

ax.set_xlabel(elem_x, fontsize=12, labelpad=8)
ax.set_ylabel(elem_y, fontsize=12, labelpad=8)
ax.set_title(f"{elem_x}  vs  {elem_y}   —   r = {corr:.3f}", fontsize=13, pad=12)
ax.spines[["top", "right"]].set_visible(False)
ax.set_facecolor("#f8f9fa")
ax.grid(True, linestyle="--", alpha=0.4, zorder=0)

plt.tight_layout()
st.pyplot(fig, use_container_width=True)

# Export
buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
buf.seek(0)
st.download_button(
    "⬇️ Télécharger le graphique (.png)",
    data=buf,
    file_name=f"correlation_{elem_x}_{elem_y}.png",
    mime="image/png"
)

# Tableau des données filtrées
with st.expander("Données utilisées"):
    st.dataframe(df_plot.style.format("{:.4g}"), use_container_width=True)
