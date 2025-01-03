import streamlit as st
import pandas as pd
from PIL import Image
import requests
from io import BytesIO

# Load the dataset
csv_file_path = "model_on_25thV2(distributors).csv"  # Replace with your CSV file
df = pd.read_csv(csv_file_path)

# Function to download an image from a URL
def download_image(url):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else:
            return None
    except Exception as e:
        return None

# Initialize flagged data storage
if "flagged_images" not in st.session_state:
    st.session_state.flagged_images = []

# Sidebar for filters
st.sidebar.title("Filters")
attribute_filter = st.sidebar.selectbox("Filter by Attribute Name", options=["All"] + list(df['attribute_name'].unique()))
entity_filter = st.sidebar.selectbox("Filter by Entity Name", options=["All"] + list(df['entity_name'].unique()))
prediction_filter = st.sidebar.selectbox("Filter by Prediction", options=["All"] + list(df['prediction'].unique()))
confidence_min = st.sidebar.slider("Minimum Confidence", min_value=0.0, max_value=1.0, value=0.0, step=0.01)
confidence_max = st.sidebar.slider("Maximum Confidence", min_value=0.0, max_value=1.0, value=1.0, step=0.01)

# Filter the dataframe based on sidebar inputs
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
    st.warning("No images found for the selected filters.")
else:
    for idx, row in filtered_df.iterrows():
        # Download and display the image
        image = download_image(row['url'])
        if image is not None:
            col1, col2, col3 = st.columns([3, 4, 1])
            with col1:
                st.image(image, use_column_width=True, caption=f"Distributor: {row['entity_name']}")
            with col2:
                st.write(f"**Attribute Name:** {row['attribute_name']}")
                st.write(f"**Prediction:** {row['prediction']}")
                st.write(f"**Confidence:** {row['confidence']:.2f}")
            with col3:
                if st.button(f"Flag Image {idx}", key=f"flag_{idx}"):
                    st.session_state.flagged_images.append({
                        "url": row['url'],
                        "attribute_name": row['attribute_name'],
                        "entity_name": row['entity_name'],
                        "prediction": row['prediction'],
                        "confidence": row['confidence']
                    })
                    st.success(f"Image flagged: {row['url']}")

# Save flagged data
st.sidebar.markdown("---")
if st.sidebar.button("Save Flagged Images"):
    if st.session_state.flagged_images:
        flagged_df = pd.DataFrame(st.session_state.flagged_images)
        flagged_df.to_csv("flagged_images.csv", index=False)
        st.sidebar.success("Flagged images saved to 'flagged_images.csv'.")
    else:
        st.sidebar.warning("No images have been flagged.")

# Summary of flagged images
if st.sidebar.checkbox("Show Flagged Images Summary"):
    if st.session_state.flagged_images:
        st.sidebar.write(pd.DataFrame(st.session_state.flagged_images))
    else:
        st.sidebar.write("No flagged images.")
