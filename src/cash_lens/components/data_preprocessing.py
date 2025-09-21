import re
import pandas as pd

# === Regex Patterns ===
amount_regex = re.compile(r'(?:rs\.?|inr)\s*[\u20B9]?\s*([\d,]+\.?\d*)', re.I)
date_regex = re.compile(r'(\d{2}/\d{2}/\d{4})')
debit_keyword = re.compile(r'\b(debit|debited|spent|withdrawn|paid|payment|purchase|pos)\b', re.I)
credit_keyword = re.compile(r'\b(credit|credited|received|salary|cashback|deposit)\b', re.I)

# === Merchant Map ===
merchant_map = {
    'zomato': 'Food',
    'swiggy': 'Food',
    'dominos': 'Food',
    'amazon': 'Shopping',
    'flipkart': 'Shopping',
    'myntra': 'Shopping',
    'uber': 'Transport',
    'ola': 'Transport',
    'paytm': 'UPI',
    'gpay': 'UPI',
    'googlepay': 'UPI',
    'phonepe': 'UPI',
    'atm': 'Cash Withdrawal',
    'salary': 'Income',
    'neft': 'Income',
    'rahul': 'UPI'
}

# === Sub-category Keywords ===
subcat_keywords = {
    'electricity bill': 'Electricity',
    'electricity': 'Electricity',
    'water bill': 'Water',
    'water': 'Water',
    'rent': 'Rent',
    'gas': 'Gas',
    'internet': 'Internet',
    'mobile': 'Mobile',
    'subscription': 'Subscription',
    'netflix': 'Subscription',
    'emi': 'EMI',
    'loan': 'Loan',
    'salary': 'Salary',
    'cashback': 'Cashback',
    'fashion': 'Fashion',
    'food': 'Dining',
    'pizza': 'Dining',
    'dominos': 'Dining',
    'myntra': 'Fashion',
    'flipkart': 'E-commerce',
    'amazon': 'E-commerce',
    'zomato': 'Dining',
    'uber': 'Ride Sharing',
    'atm': 'ATM Withdrawal',
    'phonepe': 'UPI Payment',
    'paytm': 'UPI Payment',
    'gpay': 'UPI Payment',
    'googlepay': 'UPI Payment',
    'neft': 'NEFT Transfer',
    'rahul': 'UPI Transfer'
}

# === Subcat → Category Map ===
subcat_to_category = {
    'Electricity': 'Bills',
    'Water': 'Bills',
    'Rent': 'Bills',
    'Gas': 'Bills',
    'Internet': 'Bills',
    'Mobile': 'Bills',
    'Subscription': 'Bills',
    'Fashion': 'Shopping',
    'Dining': 'Food',
    'E-commerce': 'Shopping',
    'Ride Sharing': 'Transport',
    'EMI': 'Loans/EMI',
    'Loan': 'Loans/EMI',
    'Salary': 'Income',
    'Cashback': 'Income',
    'NEFT Transfer': 'Income',
    'ATM Withdrawal': 'Cash Withdrawal',
    'UPI Transfer': 'UPI',
    'UPI Payment': 'UPI'
}

# === Subcat → Fallback Merchant ===
fallback_merchant_by_subcat = {
    'Rent': 'Landlord',
    'Electricity': 'Electricity Board',
    'Internet': 'ISP Provider',
    'Water': 'Water Department',
    'Gas': 'Gas Provider',
    'Mobile': 'Mobile Operator',
    'Subscription': 'Subscription Service',
    'EMI': 'EMI Provider',
    'Loan': 'Loan Provider',
    'UPI Payment': 'UPI Payment',
    'UPI Transfer': 'UPI Transfer',
    'ATM Withdrawal': 'ATM',
    'Salary': 'Employer',
    'Cashback': 'Cashback Source',
    'NEFT Transfer': 'Bank Transfer',
    'Dining': 'Restaurant',
    'Fashion': 'Fashion Store',
    'E-commerce': 'Online Store',
    'General Expense': 'Expense',
    'General Income': 'Income'
}


# === Core Extraction Functions ===
def extract_amount(text):
    match = amount_regex.search(text)
    if match:
        return float(match.group(1).replace(',', ''))
    return None


def extract_date(text):
    match = date_regex.search(text)
    return match.group(1) if match else "--"


def extract_direction(text):
    if debit_keyword.search(text):
        return 'Debit'
    if credit_keyword.search(text):
        return 'Credit'
    return 'Unknown'


def extract_subcategory_from_text(text):
    lower = text.lower()
    for key in sorted(subcat_keywords.keys(), key=lambda x: -len(x)):
        if key in lower:
            return subcat_keywords[key]
    return None


def determine_category_and_subcategory(text, merchant, direction):
    subcat = extract_subcategory_from_text(text)
    if subcat:
        category = subcat_to_category.get(subcat, 'Other')
        return category, subcat

    if merchant and merchant.lower() in subcat_keywords:
        subcat = subcat_keywords[merchant.lower()]
        category = subcat_to_category.get(subcat, 'Other')
        return category, subcat

    fallback_subcat_map = {
        'atm': 'ATM Withdrawal',
        'uber': 'Ride Sharing',
        'amazon': 'E-commerce',
        'flipkart': 'E-commerce',
        'zomato': 'Dining',
        'dominos': 'Dining',
        'myntra': 'Fashion',
        'salary': 'Salary',
        'neft': 'NEFT Transfer',
        'rahul': 'UPI Transfer'
    }

    if merchant.lower() in fallback_subcat_map:
        subcat = fallback_subcat_map[merchant.lower()]
        category = subcat_to_category.get(subcat, 'Other')
        return category, subcat

    # Final fallback
    if direction == 'Credit':
        return 'Income', 'General Income'
    elif direction == 'Debit':
        return 'Expense', 'General Expense'

    return 'Other', 'General'


def extract_merchant(text, sub_category=None):
    text_lower = text.lower()

    for known in merchant_map:
        if re.search(r'\b' + re.escape(known) + r'\b', text_lower):
            return known.capitalize()

    # Try extracting merchant after keywords
    m = re.search(r'\b(?:at|to|via|from|on)\s+([A-Za-z][A-Za-z&\.\-\s]{1,30})', text, re.I)
    if m:
        candidate = m.group(1).strip()
        words = [w for w in candidate.split() if not w.isdigit()]
        if words:
            return " ".join(words[:2]).title()

    # Fallback: use sub_category to infer a pseudo-merchant
    if sub_category and sub_category in fallback_merchant_by_subcat:
        return fallback_merchant_by_subcat[sub_category]

    return "Unknown"


def classify_transaction(text):
    amount = extract_amount(text)
    date = extract_date(text)
    direction = extract_direction(text)

    # First attempt to extract merchant
    initial_merchant = extract_merchant(text)
    category, sub_category = determine_category_and_subcategory(text, initial_merchant, direction)

    # Try to get a better merchant if initial is unknown
    merchant = extract_merchant(text, sub_category=sub_category)

    return {
        'date': date,
        'amount': amount,
        'merchant': merchant,
        'category': category,
        'sub_category': sub_category,
        'direction': direction
    }

# === Main Logic ===
if __name__ == "__main__":
    input_path = "data/new.csv"
    output_path = "data/new_cleaned.csv"

    df = pd.read_csv(input_path)

    parsed = df['text'].apply(classify_transaction)
    parsed_df = pd.DataFrame(parsed.tolist())

    final_df = pd.concat([df, parsed_df], axis=1)

    # Export
    final_df.to_csv(output_path, index=False)

    print("✅ Cleaned CSV generated at:", output_path)
    print(final_df.head(10))
