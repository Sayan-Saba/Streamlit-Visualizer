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

# Function to download images
def download_image(url):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else:
            return None
    except Exception:
        return None

# Initialize session state for flagged images
if "flagged_images" not in st.session_state:
    st.session_state.flagged_images = []

# Sidebar theme toggle
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

# Sidebar filters
with st.sidebar:
    st.title("Filters")
    attribute_filter = st.selectbox("Filter by Attribute Name", options=["All"] + list(df['attribute_name'].unique()))
    entity_filter = st.selectbox("Filter by Entity Name", options=["All"] + list(df['entity_name'].unique()))
    prediction_filter = st.selectbox("Filter by Prediction", options=["All"] + list(df['prediction'].unique()))
    confidence_min = st.slider("Minimum Confidence", min_value=0.0, max_value=1.0, value=0.0, step=0.01)
    confidence_max = st.slider("Maximum Confidence", min_value=0.0, max_value=1.0, value=1.0, step=0.01)

    # Save flagged images to CSV
    if st.button("Download Flagged Images as CSV"):
        flagged_df = pd.DataFrame(st.session_state.flagged_images, columns=df.columns)
        csv = flagged_df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="flagged_images.csv">Download CSV</a>'
        st.markdown(href, unsafe_allow_html=True)

# Apply filters
filtered_df = df.copy()
if attribute_filter != "All":
    filtered_df = filtered_df[filtered_df['attribute_name'] == attribute_filter]
if entity_filter != "All":
    filtered_df = filtered_df[filtered_df['entity_name'] == entity_filter]
if prediction_filter != "All":
    filtered_df = filtered_df[filtered_df['prediction'] == prediction_filter]
filtered_df = filtered_df[(filtered_df['confidence'] >= confidence_min) & (filtered_df['confidence'] <= confidence_max)]

# Display images
st.title("Image Visualization and Flagging")

if filtered_df.empty:
    st.warning("No images match the selected filters.")
else:
    cols_per_row = 5  # Number of images per row
    for row_idx in range(0, len(filtered_df), cols_per_row):
        row = filtered_df.iloc[row_idx:row_idx + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, (_, row_data) in zip(cols, row.iterrows()):
            image = download_image(row_data['url'])
            if image is not None:
                with col:
                    st.markdown(
                        f"""
                        <div style="position:relative;">
                            <button style="position:absolute;top:5px;left:5px;z-index:10;background-color:red;color:white;border:none;padding:3px;cursor:pointer;"
                            onClick="flagImage('{row_data.name}')">🚩</button>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.image(image, use_column_width=True)
                    st.markdown(f"**Attribute:** {row_data['attribute_name']}")
                    st.markdown(f"**Prediction:** {row_data['prediction']}")
                    st.markdown(f"**Confidence:** {row_data['confidence']:.2f}")

# JavaScript function for flagging images
flag_image_js = """
<script>
    const flagImage = (rowId) => {
        Streamlit.setComponentValue({ flaggedId: rowId });
    };
</script>
"""
st.markdown(flag_image_js, unsafe_allow_html=True)
