import io
import streamlit as st
from datetime import date
from common import ask, make_pdf, page_setup

page_setup("LegalEase", "⚖️", "AI-powered legal document generator")
st.warning("⚠️ AI-generated drafts are for reference only and are NOT legal advice. Have a qualified lawyer review any document before use.")

DOCS = {
    "Rental / Lease Agreement": ["Landlord name", "Tenant name", "Property address", "Monthly rent", "Security deposit",
                                 "Lease start date", "Lease duration (months)"],
    "Non-Disclosure Agreement (NDA)": ["Disclosing party", "Receiving party", "Purpose of disclosure",
                                       "Confidentiality period (years)", "Effective date"],
    "Affidavit": ["Deponent name", "Father's/Spouse's name", "Address", "Purpose of affidavit", "Statement of facts"],
    "Employment Offer Letter": ["Company name", "Candidate name", "Job title", "Annual salary", "Joining date",
                                "Probation period (months)"],
    "Freelance / Service Agreement": ["Client name", "Service provider name", "Scope of work", "Total fee",
                                      "Payment schedule", "Deadline"],
    "Loan Agreement": ["Lender name", "Borrower name", "Loan amount", "Interest rate (% per year)", "Repayment period",
                       "Repayment terms"],
    "Power of Attorney": ["Principal name", "Attorney (agent) name", "Powers granted", "Duration", "Address"],
}
LANGS = ["English", "Hindi", "Tamil", "Telugu", "Kannada", "Malayalam", "Marathi", "Bengali"]

with st.sidebar:
    doc_type = st.selectbox("Document type", list(DOCS))
    lang = st.selectbox("Language", LANGS)
    tone = st.selectbox("Style", ["Formal legal", "Simple & readable"])

st.subheader(f"Details for: {doc_type}")
vals = {}
cols = st.columns(2)
for i, f in enumerate(DOCS[doc_type]):
    vals[f] = cols[i % 2].text_input(f, key=f"{doc_type}_{f}")
vals["Jurisdiction / City & State"] = cols[0].text_input("Jurisdiction / City & State")
vals["Date of document"] = str(cols[1].date_input("Date of document", date.today()))
extra = st.text_area("Additional terms or special conditions (optional)")

SYSTEM = ("You are a legal drafting assistant. Draft complete, well-structured documents with a title, parties, "
          "recitals, numbered clauses, governing law, signature blocks and witnesses where relevant. Use [__________] "
          "for any missing detail. Never invent facts. Add a one-line note that this is not legal advice.")

if st.button("Generate document", type="primary"):
    filled = {k: v for k, v in vals.items() if v}
    if len(filled) < 3:
        st.warning("Please fill in more details.")
    else:
        with st.spinner("Drafting..."):
            out = ask(f"Draft a {doc_type} in {lang}, style: {tone}.\nDetails: {filled}\nAdditional terms: {extra or 'none'}",
                      SYSTEM, temperature=0.2)
        if out:
            st.session_state.draft = out
            st.session_state.dtype = doc_type
            st.session_state.dlang = lang
            st.session_state.pop("explain", None)

if st.session_state.get("draft"):
    st.subheader("Your draft (editable)")
    draft = st.text_area("Edit before exporting", key="draft", height=420, label_visibility="collapsed")
    title = st.session_state.get("dtype", "Document")

    if st.button("Explain clauses in plain language"):
        with st.spinner("Explaining..."):
            st.session_state.explain = ask(
                f"Explain each clause of this document in simple plain {st.session_state.dlang}, and flag any risks "
                f"or points the signer should double-check:\n\n{draft}", "You are a helpful legal explainer.", temperature=0.3)
    if st.session_state.get("explain"):
        st.info(st.session_state.explain)

    def make_docx(t, text):
        from docx import Document
        d = Document()
        d.add_heading(t, 0)
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                d.add_heading(line.lstrip("# ").replace("**", ""), 2)
            elif line:
                d.add_paragraph(line.replace("**", ""))
        buf = io.BytesIO()
        d.save(buf)
        return buf.getvalue()

    c = st.columns(3)
    if st.session_state.get("dlang") == "English":
        c[0].download_button("⬇️ PDF", make_pdf(title, draft), "document.pdf")
    else:
        c[0].caption("PDF export supports English only. Use DOCX for other languages.")
    c[1].download_button("⬇️ Word (DOCX)", make_docx(title, draft), "document.docx")
    c[2].download_button("⬇️ Text", draft, "document.txt")
