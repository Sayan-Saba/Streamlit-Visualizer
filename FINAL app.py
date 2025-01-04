import streamlit as st
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
import base64

# Set page config
st.set_page_config(page_title="Image Visualization", layout="wide", initial_sidebar_state="collapsed")

# Load dataset
csv_file_path = "image_data.csv"  # Replace with your CSV file path
df = pd.read_csv(csv_file_path)

# Caching the image download to improve performance
@st.cache_data
def download_image(url):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except Exception:
        return None
    return None

# Initialize session state
if "filtered_df" not in st.session_state:
    st.session_state.filtered_df = df.copy()
if "flagged_images" not in st.session_state:
    st.session_state.flagged_images = []

# Sidebar for theme toggle
theme = st.sidebar.radio("Theme", ["Light", "Dark"], index=0)

# JavaScript for toggling themes
theme_toggle_js = """
    <script>
        const toggleTheme = () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
        };
        document.documentElement.setAttribute('data-theme', 'light');
    </script>
"""
st.markdown(theme_toggle_js, unsafe_allow_html=True)
st.markdown(f"<script>document.documentElement.setAttribute('data-theme', '{theme.lower()}')</script>", unsafe_allow_html=True)

# Sidebar for filters
with st.sidebar:
    st.title("Filters")
    attribute_filter = st.selectbox("Filter by Attribute Name", options=["All"] + list(df['attribute_name'].unique()))
    entity_filter = st.selectbox("Filter by Entity Name", options=["All"] + list(df['entity_name'].unique()))
    prediction_filter = st.selectbox("Filter by Prediction", options=["All"] + list(df['prediction'].unique()))
    confidence_min = st.slider("Minimum Confidence", min_value=0.0, max_value=1.0, value=0.0, step=0.01)
    confidence_max = st.slider("Maximum Confidence", min_value=0.0, max_value=1.0, value=1.0, step=0.01)

    # Apply filters
    if st.button("Apply Filters"):
        st.session_state.filtered_df = df.copy()
        if attribute_filter != "All":
            st.session_state.filtered_df = st.session_state.filtered_df[
                st.session_state.filtered_df['attribute_name'] == attribute_filter
            ]
        if entity_filter != "All":
            st.session_state.filtered_df = st.session_state.filtered_df[
                st.session_state.filtered_df['entity_name'] == entity_filter
            ]
        if prediction_filter != "All":
            st.session_state.filtered_df = st.session_state.filtered_df[
                st.session_state.filtered_df['prediction'] == prediction_filter
            ]
        st.session_state.filtered_df = st.session_state.filtered_df[
            (st.session_state.filtered_df['confidence'] >= confidence_min) & 
            (st.session_state.filtered_df['confidence'] <= confidence_max)
        ]

# Main display for image visualization and flagging
st.title("Image Visualization and Flagging")

if st.session_state.filtered_df.empty:
    st.warning("No images match the selected filters.")
else:
    cols_per_row = 5  # Number of images per row
    for row_idx in range(0, len(st.session_state.filtered_df), cols_per_row):
        row = st.session_state.filtered_df.iloc[row_idx:row_idx + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, (_, row_data) in zip(cols, row.iterrows()):
            image = download_image(row_data['url'])
            if image is not None:
                with col:
                    # Display image and labels
                    st.image(image, use_column_width=True)
                    st.markdown(f"**Attribute:** {row_data['attribute_name']}")
                    st.markdown(f"**Prediction:** {row_data['prediction']}")
                    st.markdown(f"**Confidence:** {row_data['confidence']:.2f}")

                    # Flag button
                    if st.button("Flag", key=f"flag_{row_data.name}"):
                        if row_data.to_dict() not in st.session_state.flagged_images:
                            st.session_state.flagged_images.append(row_data.to_dict())
                            st.success(f"Image flagged!")
                        else:
                            st.warning("Image already flagged.")

# Download button for flagged images
if st.session_state.flagged_images:
    flagged_df = pd.DataFrame(st.session_state.flagged_images)
    csv = flagged_df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    download_href = f'<a href="data:file/csv;base64,{b64}" download="flagged_images.csv">Download Flagged Images</a>'
    st.markdown(download_href, unsafe_allow_html=True)
else:
    st.info("No flagged images available to download.")
