import streamlit as st
import pandas as pd
import spacy
import pdfplumber
from transformers import pipeline

# Load NLP models
nlp = spacy.load("en_core_web_sm")
ner_pipeline = pipeline("ner", model="dslim/bert-base-NER")



# Function to extract text from a PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

# Function to extract rules from the PDF text
def extract_rules(text):
    doc = nlp(text)
    extracted_rules = []

    for sent in doc.sents:
        entities = ner_pipeline(sent.text)
        conditions = [ent['word'] for ent in entities if ent['entity'].startswith("B-")]

        # Identify rule-related keywords
        keywords = ["must", "should", "shall", "not allowed", "cannot", "only if", "required"]
        if any(word in sent.text.lower() for word in keywords):
            structured_rule = {
                "rule": sent.text,
                "conditions": conditions,
                "field": "Account_Balance" if "account balance" in sent.text.lower() else 
                         "RiskScore" if "risk score" in sent.text.lower() else
                         "Transaction_Amount" if "transaction amount" in sent.text.lower() else None,
                "operator": "< 0" if "not be negative" in sent.text.lower() else 
                            "> 5" if "greater than 5" in sent.text.lower() else
                            "==" if "must match" in sent.text.lower() else None
            }
            extracted_rules.append(structured_rule)

    return extracted_rules

# Function to validate rules against CSV data
def validate_rules(rules, df):
    validation_results = []

    for rule in rules:
        st.write("hello")
        #rule_text = rule["rule"].lower()
        field = rule["field"]
        operator = rule["operator"]
        condition = rule.get('condition')
        validation_type = rule.get('validation_type')

        
        
        if field and operator:
            # Build condition dynamically
            query = f"{field} {operator}"
            violations = df.query(query)

            if not violations.empty:
                validation_results.append(f"❌ Violation: {rule['rule']} - {violations.to_dict(orient='records')}")

        # Rule: Account balance must not be negative
        if "account balance" in rule_text and "not be negative" in rule_text:
            negative_balances = df[df['Account_Balance'].astype(float) < 0]
            if not negative_balances.empty:
                validation_results.append(f"❌ Violation: Negative account balances found - {negative_balances.to_dict(orient='records')}")

        # Rule: Customers with a high risk score require review
        if "risk score" in rule_text and "greater than 5" in rule_text:
            high_risk = df[df['RiskScore'].astype(float) > 5]
            if not high_risk.empty:
                validation_results.append(f"❌ Violation: High-risk customers found - {high_risk.to_dict(orient='records')}")

        # Rule: Reported amount must match transaction amount
        if "reported amount" in rule_text and "must match transaction amount" in rule_text:
            mismatched_amounts = df[df['Transaction_Amount'].astype(float) != df['Reported_Amount'].astype(float)]
            if not mismatched_amounts.empty:
                validation_results.append(f"❌ Violation: Mismatched transaction amounts - {mismatched_amounts.to_dict(orient='records')}")

       
    return validation_results if validation_results else ["✅ No violations found!"]

# Streamlit UI
st.title("📜 Rule Extraction & Validation from PDF")
st.sidebar.header("Upload Files")

# Upload PDF
uploaded_pdf = st.sidebar.file_uploader("Upload a PDF file", type=["pdf"])

# Upload CSV
uploaded_csv = st.sidebar.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_pdf and uploaded_csv:
    st.success("✅ Files uploaded successfully!")

    # Extract text from PDF
    pdf_text = extract_text_from_pdf(uploaded_pdf)
    st.subheader("📄 Extracted Text from PDF")
    st.text_area("Extracted Text", pdf_text[:1000], height=200)

    # Extract rules
    rules = extract_rules(pdf_text)
    st.subheader("📜 Extracted Rules")
    for idx, rule in enumerate(rules, 1):
        st.write(f"**{idx}.** {rule['rule']} (Conditions: {rule['conditions']})")

    # Load CSV
    df = pd.read_csv(uploaded_csv)

    # Validate rules against CSV
    validation_results = validate_rules(rules, df)
    st.subheader("✅ Validation Results")
    for result in validation_results:
        st.write(result)

else:
    st.warning("⚠️ Please upload both a PDF and a CSV file.")
