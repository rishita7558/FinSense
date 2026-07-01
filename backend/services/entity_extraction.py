import spacy
from spacy.matcher import PhraseMatcher
import spacy.cli

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

financial_keywords = [
    # ── Loans & Credit ──
    "loan", "home loan", "personal loan", "car loan", "vehicle loan",
    "education loan", "business loan", "gold loan", "loan against property",
    "emi", "equated monthly installment", "installment",
    "mortgage", "refinance", "collateral", "guarantor",
    "credit", "credit card", "credit score", "credit limit",
    "debit card", "overdraft", "line of credit",
    "debt", "repayment", "foreclosure", "prepayment",
    "principal", "tenure", "down payment",

    # ── Investments ──
    "investment", "invest", "portfolio", "returns", "yield",
    "sip", "systematic investment plan", "lump sum", "lumpsum",
    "mutual fund", "mf", "equity", "equity fund", "debt fund",
    "index fund", "etf", "exchange traded fund",
    "stock", "share", "nifty", "sensex", "bse", "nse",
    "ipo", "dividend", "capital gain", "capital gains",
    "bonds", "debenture", "government bond", "sovereign bond",
    "gold", "gold bond", "sgb", "sovereign gold bond",
    "real estate", "property", "reit",
    "commodity", "futures", "options", "derivatives",
    "hedge fund", "venture capital",

    # ── Savings & Deposits ──
    "savings", "savings account", "current account",
    "fd", "fixed deposit", "rd", "recurring deposit",
    "deposit", "bank deposit", "term deposit",
    "ppf", "public provident fund",
    "nsc", "national savings certificate",
    "sukanya samriddhi", "senior citizen savings",

    # ── Insurance ──
    "insurance", "life insurance", "health insurance",
    "term insurance", "term plan", "endowment plan",
    "ulip", "unit linked", "mediclaim",
    "premium", "sum assured", "claim", "coverage",
    "rider", "nominee", "beneficiary",
    "motor insurance", "vehicle insurance",

    # ── Retirement & Pension ──
    "pension", "nps", "national pension",
    "retirement", "retirement fund", "annuity",
    "pf", "provident fund", "epf", "employee provident fund",
    "gratuity", "superannuation",

    # ── Tax ──
    "tax", "income tax", "gst", "tds",
    "tax saving", "tax deduction", "section 80c", "80c",
    "section 80d", "80d", "hra", "tax return",
    "capital gains tax", "long term capital gain", "short term capital gain",
    "tax exemption", "tax rebate",

    # ── Banking ──
    "bank", "account", "balance", "transaction",
    "upi", "neft", "rtgs", "imps", "cheque", "demand draft",
    "kyc", "pan card", "aadhaar", "cibil",
    "interest", "interest rate", "repo rate", "base rate",
    "compound interest", "simple interest",
    "net banking", "mobile banking",

    # ── Monetary ──
    "rupees", "lakh", "lakhs", "crore", "crores",
    "percent", "percentage", "per annum",
    "monthly", "annual", "quarterly", "yearly",
    "financial", "funds", "scheme", "plan",
    "budget", "expense", "income", "salary", "revenue", "profit", "loss",
    "inflation", "gdp",

    # ── Hindi / Regional financial terms ──
    "udhaar", "karz", "kist", "qist", "nivesh", "bima", "beema",
    "byaaj", "vyaj", "share bazaar", "girvi", "khata",
    "bachat", "jama", "paisa", "dhan", "munafa", "nuksan"
]

patterns = [nlp.make_doc(text) for text in financial_keywords]
matcher.add("FINANCIAL_TERMS", patterns)


def extract_financial_entities(text):
    doc = nlp(text)
    matches = matcher(doc)

    # Collect all numerical/money values
    amounts = []
    for ent in doc.ents:
        if ent.label_ in ["MONEY", "CARDINAL", "QUANTITY", "PERCENT"]:
            amounts.append(ent)

    detected = []
    seen_keywords = set()
    
    for match_id, start, end in matches:
        span = doc[start:end]
        keyword = span.text.lower()
        
        # Skip duplicates
        if keyword in seen_keywords:
            continue
        seen_keywords.add(keyword)
        
        # Look for the closest amount within a 10-word window
        associated_amount = None
        min_distance = 11
        
        for amt in amounts:
            distance = min(abs(amt.start - end), abs(start - amt.end))
            if distance < min_distance:
                min_distance = distance
                associated_amount = amt.text
        
        entity_record = {"entity": keyword}
        if associated_amount:
            entity_record["amount"] = associated_amount
            
        detected.append(entity_record)

    return detected