import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import pandas as pd
import os
from io import BytesIO

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Hot Mess Coach", page_icon="🔥")

st.title("🔥 Hot Mess Coach")
st.write("Your supportive mini mental coach powered by gpt-4o-mini.")

# --- Upload section ---
uploaded_file = st.file_uploader("Upload PDF or CSV (optional)", type=["pdf", "csv"])

uploaded_content = None

def extract_pdf_text(pdf_bytes):
    """Extract text from PDF using PyPDF2."""
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        return f"[PDF extraction error]: {str(e)}"

if uploaded_file:
    if uploaded_file.type == "text/csv":
        df = pd.read_csv(uploaded_file)
        uploaded_content = df.to_string()
        st.write("📄 **CSV Loaded:**")
        st.dataframe(df)

    elif uploaded_file.type == "application/pdf":
        pdf_bytes = uploaded_file.read()
        extracted_text = extract_pdf_text(pdf_bytes)
        uploaded_content = extracted_text
        st.write("📄 **PDF Extracted Text:**")
        st.text_area("Extracted Text", extracted_text, height=200)

# --- Chat section ---
user_msg = st.text_area("How are you feeling today?", "I feel like a hot mess today...")

if st.button("Coach me"):
    with st.spinner("Thinking..."):
        system_prompt = "You are a supportive mental coach who helps overwhelmed people feel calmer."

        # Include uploaded content in prompt if available
        if uploaded_content:
            system_prompt += f"\n\nThe user has also uploaded a document. Here is the content:\n{uploaded_content}"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
        )

        reply = response.choices[0].message.content

        st.subheader("💬 Coach says:")
        st.write(reply)

#uv run streamlit run STEP4_app_llm_st_doc.py