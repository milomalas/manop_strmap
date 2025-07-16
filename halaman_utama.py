import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
import folium.plugins
from streamlit_folium import st_folium


### Global Variables ###
########################
PAGE_TITLE = "Peta Jaringan Alat Pengamatan BMKG"

ALAT_DESCS = {
    "AWS": {
        "full name":"Automatic Weather Station",
        "icon":":cloud:", 
        "icon_fa":"cloud",
        "color":"blue",
    },
    "AAWS": {
        "full name":"Automatic Agroclimate Weather Station",
        "icon":":corn:",
        "icon_fa":"leaf",
        "color":"green",
    },
    "ARG": {
        "full name":"Automatic Rain Gauge",
        "icon":":droplet:",
        "icon_fa":"droplet",
        "color":"darkblue",
    },
    "IKRO": {
        "full name":"Pengamatan Iklim Mikro",
        "icon":":golf:",
        "icon_fa":"map-signs",
        "color":"purple",
    },
    "ASRS": {
        "full name":"Automatic Solar Radiation Station",
        "icon":":high_brightness:", 
        "icon_fa":"sun",
        "color":"orange",
    },
}

PULAU_PROVS = {
    "Sumatera": [
        "Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Kepulauan Riau",
        "Jambi", "Bengkulu", "Sumatera Selatan", "Kepulauan Bangka Belitung", "Lampung"
    ],
    "Kalimantan": [
        "Kalimantan Barat", "Kalimantan Tengah", "Kalimantan Selatan", 
        "Kalimantan Timur", "Kalimantan Utara"
    ],
    "Jawa":[
        "Banten", "Jawa Barat", "DKI Jakarta", "Jawa Tengah", "DI Yogyakarta", "Jawa Timur",
    ],
    "Bali Nusa Tenggara":[
        "Bali", "Nusa Tenggara Barat", "Nusa Tenggara Timur"
    ],
    "Sulawesi":[
        "Sulawesi Utara", "Gorontalo", "Sulawesi Tengah", "Sulawesi Barat", 
        "Sulawesi Selatan", "Sulawesi Tenggara"
    ],
    "Maluku":[
        "Maluku", "Maluku Utara"
    ],
    "Papua":[
        "Papua Barat", "Papua"
    ],
}

DFVAR = {
    "PROV" : "nama_propinsi",
    "TYPE" : "type",
    "NAME" : "name_station",
    "ID"   : "id_station",
    "LAT"  : "latt_station",
    "LON"  : "long_station",
    "ELEV" : "elv_station",
    "CITY" : "nama_kota",
    "DISTR": "kecamatan",
}

## ---- CSS ---- ##
with open("./style.css", mode="r", encoding="utf-8") as css:
    st.markdown( f"<style>{css.read()}</style>", unsafe_allow_html=True)

### Helper Functions ###
########################
@st.cache_data
def load_full_gdf():
    '''Load prepared GeoDataFrame data.'''
    data_dir = "data_geo/"
    # gdf = gpd.read_file(data_dir + "Metadata_tes_provIntersect.geojson") # Test
    gdf = gpd.read_file(data_dir + "Metadata.geojson")
    return gdf

def warn_nodata():
    st.warning("No data to view!", icon=":material/database_off:")

## ---- Callback functions ---- ##
def prepend_alat_icons(opt):
    '''If `opt` is listed in `ALAT_DESC`, prepend corresponding `icon`s to it.'''
    if opt in set(ALAT_DESCS):
        return f"{ALAT_DESCS[opt]['icon']} {opt}"
    else:
        return opt

def sel_prov_add(opts, pulau):
    '''
    Modify session state `st.session_state["sel_prov_keys"]`, adding the intersection of 
    `PULAU_PROVS["pulau"]` list and all available options `opts` into the session state.
    If `**Pilih semua**`, simply replace said session with `opts`.
    '''
    if pulau=="**Pilih semua**":
        st.session_state["sel_prov_keys"] = opts
    else:
        sel_prov_old   = frozenset(st.session_state["sel_prov_keys"])
        opts_intersect = frozenset(opts).intersection(frozenset(PULAU_PROVS[pulau]))
        st.session_state["sel_prov_keys"] = list(sel_prov_old.union(opts_intersect))

def on_change_tipeAlat():
    '''
    Changes to `st.session_state["sel_prov_keys"]` when 
    tipeAlat selection (`sel_tipeAlat`) is modified.
    '''
    # Filter provinsi selection changes based on newest current available options
    sel_tipeAlat = st.session_state["sel_tipeAlat_keys"]
    # if "sel_prov_state" in st.session_state:
    sel_prov_old = st.session_state["sel_prov_keys"]

    if len(sel_prov_old)>0:
        df_full        = load_full_gdf()
        df_filtered    = df_full[df_full[DFVAR["TYPE"]].isin(sel_tipeAlat)]
        new_valid_prov = df_filtered[DFVAR["PROV"]].unique().tolist()

        sel_prov_intersect = frozenset(sel_prov_old).intersection(frozenset(new_valid_prov))
        st.session_state["sel_prov_keys"] = list(sel_prov_intersect)

## ---- Tab contents ---- ###
def GISMap_render_img():
    '''
    1. Add segmented control buttons to select image to view.
    2. View image with `st.image`. If no image is selected, show info callout.
    '''
    opts_GISimg = ALAT_DESCS.keys()
    sel_GISimg  = st.segmented_control(
        "Pilih peta:",
        label_visibility="visible",
        options=opts_GISimg,
        selection_mode="single",
        format_func=prepend_alat_icons,
    )
    path_img = f"data_img/Peta {sel_GISimg}.png"

    if sel_GISimg:
        with st.container(border=True):
            st.image(
                path_img,
                caption=f"{ALAT_DESCS[sel_GISimg]["full name"]}"
                         " - Rendered with QGIS",
                use_container_width=True,
            )
        with st.columns(5)[2]:
            with open(path_img, "rb") as f:
                st.download_button(
                    "Unduh gambar",
                    data=f,
                    file_name=f"Peta {sel_GISimg}.png",
                    # type="primary",
                    disabled=(sel_GISimg is None),
                    use_container_width=True,
                )

    else:
        st.info("Pilih peta terlebih dahulu.", icon=":material/info:")

def ActiveMap_df_filter(full_df):
    '''
    Multi-select inputs and buttons for DataFrame filter. Query the full DataFrame
    based on said inputs and returns the filtered DataFrame.
    '''
    # Session states initialisations for the filters
    if "sel_tipeAlat_keys" not in st.session_state:
        st.session_state["sel_tipeAlat_keys"] = []

    if "sel_prov_keys" not in st.session_state:
        st.session_state["sel_prov_keys"] = []

    if "sel_pulau_keys" not in st.session_state:
        st.session_state["sel_pulau_keys"] = ["Pilih semua"]

    # Filter tipeAlat
    st.text("Pilih tipe alat:")

    opts_tipeAlat = full_df[DFVAR["TYPE"]].unique().tolist()
    opts_tipeAlat = (
        list(ALAT_DESCS.keys())
        + sorted(list( frozenset(opts_tipeAlat) - set(ALAT_DESCS.keys()) ))
    )
    sel_tipeAlat  = st.pills(
        "Pilih tipe alat:",
        label_visibility="collapsed",
        options=opts_tipeAlat,
        format_func=prepend_alat_icons,
        selection_mode="multi",
        key="sel_tipeAlat_keys",
        on_change=on_change_tipeAlat,
    )

    df_filtered = full_df[full_df[DFVAR["TYPE"]].isin(sel_tipeAlat)]

    # Filter provinsi
    st.text("Pilih provinsi:")
    opts_prov = df_filtered[DFVAR["PROV"]].unique().tolist()
    disable_sel_prov = (len(opts_prov)==0)

    pulau_buttons = ["**Pilih semua**"] + list(PULAU_PROVS.keys())
    for pulau_i,col_i in zip(pulau_buttons, st.columns(len(pulau_buttons)) ):
        with col_i:
            st.button(
                pulau_i,
                type="secondary",
                use_container_width=True,
                on_click=sel_prov_add,
                kwargs={"opts":opts_prov, "pulau":pulau_i},
                disabled=disable_sel_prov,
                key=f"button_{pulau_i}",
            )

    sel_prov = st.multiselect(
        "Pilih provinsi:",
        label_visibility="collapsed",
        options=opts_prov,
        # default=st.session_state["sel_prov_keys"],
        key="sel_prov_keys",
        disabled=disable_sel_prov,
    )

    df_filtered = df_filtered[df_filtered[DFVAR["PROV"]].isin(sel_prov)]
    return df_filtered

def ActiveMap_folium(filtered_df):
    '''Draw Folium map'''
    # Map base
    m_center = (-2,118)
    m_maxbds = [(-12,93),(8,143)]
    m = folium.Map(
        location=m_center,
        tiles=None,
        zoom_start=5,
        control_scale=True,
        width="100%",
        height="75%",
        min_lat=m_maxbds[0][0], max_lat=m_maxbds[1][0],
        min_lon=m_maxbds[0][1], max_lon=m_maxbds[1][1],
        max_bounds=True,
    )
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)
    folium.TileLayer("Cartodb Positron", name="CartoDB Positron").add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC",
        name="ESRI NatGeoWorldMap",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Source: Esri",
        name="ESRI WorldShadedRelief",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
        name="ESRI WorldImagery",
    ).add_to(m)

    # Prov count for MarkerCluster groups
    list_prov = filtered_df[DFVAR["PROV"]].unique().tolist()

    # MarkerCluster toggle
    chk_cluster = st.checkbox("Cluster markers", value=True)
    if chk_cluster:
        # Make prov cluster groups (if toggled)
        list_fg = [
            folium.plugins.MarkerCluster(
                name=f"Provinsi {iprov}",
                popups=f"Provinsi {iprov}",
                control=False,
            ).add_to(m)
            for iprov in list_prov
        ]
    else:
        # Add straight to map
        list_fg = [m for _ in list_prov]

    # Iterating per type
    for ftype, ftype_attr in ALAT_DESCS.items():
        fgdf = filtered_df[filtered_df[DFVAR["TYPE"]] == ftype]

        # Marker icon appearance
        ficon = folium.Icon(
            color=ftype_attr["color"],
            icon=ftype_attr["icon_fa"],
            prefix="fa",
        )

        if len(fgdf)>0:
            #Iterate per prov (clusters)
            for iprov, ifg in zip(list_prov, list_fg):
                fgdf_iprov = fgdf[fgdf[DFVAR["PROV"]] == iprov]

                # Iterate points adding markers
                for pts in fgdf_iprov.itertuples():
                    popup_txt = f"""
                        <center><h4><b>{getattr(pts,DFVAR["ID"])}</b></h4></center>
                        <center>{getattr(pts,DFVAR["NAME"])}</center>
                        <hr>
                        <b>Tipe alat:</b> {ALAT_DESCS[getattr(pts, DFVAR["TYPE"])]["full name"]}<br>
                        <b>Site ID:</b> {getattr(pts, DFVAR["ID"])}<br>
                        <b>Provinsi:</b> {getattr(pts, DFVAR["PROV"])}<br>
                        <b>Kab/kota:</b> {getattr(pts, DFVAR["DISTR"])}<br>
                        <b>Koordinat:</b> ({getattr(pts, DFVAR["LAT"]):.3f}, {getattr(pts, DFVAR["LON"]):.3f})<br>
                        <b>Elevasi:</b> {getattr(pts, DFVAR["ELEV"]) if pd.notna(getattr(pts, DFVAR["ELEV"])) else "N/A"} m<br>
                        """

                    folium.Marker(
                        location=(getattr(pts,DFVAR["LAT"]), getattr(pts,DFVAR["LON"])),
                        popup=folium.Popup(popup_txt, max_width=300),
                        icon=ficon,
                    ).add_to(ifg)


    folium.LayerControl(collapsed=True,).add_to(m)
    return m

## ---- Tab contents callback functions ---- ###
def call_ActiveMap(df, m_engine):
    if m_engine == "No map":
        pass
    elif len(df)>0:
        if m_engine == "Folium":
            m_folium = ActiveMap_folium(df)
            st_folium(m_folium, use_container_width=True)
        else:
            st.info("Not yet implemented!", icon=":material/no_sim:")
    else:
        warn_nodata()

### Main Function ###
#####################
def main():
    ## ---- Configs ---- ##
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=":signal_strength:",
        layout="wide",
        initial_sidebar_state="expanded",
        )

    st.title(PAGE_TITLE)
    st.caption("Tugas dashboard **:streamlit: Streamlit** dari Bidang Manajemen Operasional.")

    gdf_metadata = load_full_gdf()

    ## ---- Tabs ---- ##
    tabs = st.tabs(["GIS Map", "Interactive Map", "Custom Map"])

    with tabs[0]:
        # st.info("Under construction. Coming soon!", icon="⚒️")
        # Show GIS map PNGs/JPEGs
        GISMap_render_img()

    with tabs[1]:
        st.info("Under construction. Coming soon!", icon="⚒️")
        with st.container(border=True):
            # Filter
            gdf_filtered = ActiveMap_df_filter(gdf_metadata)
            df_filtered  = pd.DataFrame(gdf_filtered.drop(columns="geometry")) # convert to ordinary DataFrame; buggy GeoDataFrame geometry
            disable_map  = len(df_filtered)==0

            # Map render with button
            col_render =  st.columns([8,2])
            with col_render[0]:
                m_engine = st.radio(
                    label="Map engine:",
                    label_visibility="visible",
                    options=["No map", "Folium", "PyDeck"],
                    horizontal=True,
                    disabled=disable_map,
                )

        # Map render right away
        call_ActiveMap(df_filtered, m_engine)

        # Show DataFrame with a toggle
        st.divider()
        if st.toggle("Tampilkan tabel"):
            if len(df_filtered):
                st.dataframe(df_filtered)
            else:
                warn_nodata()
            st.divider()

    with tabs[2]:
        st.info("Under construction. Coming soon!", icon="⚒️")

    ## ---- end main() ---- ##


### Execution ###
#################
if __name__ == "__main__":
    main()
