"""
RAGAS Evaluation Dataset

Test queries covering different policies in the knowledge base.
Each query includes ground truth answer extracted from policy documents.
"""

EVALUATION_DATASET = [
    # Address Update Queries (from address_update_policy.md)
    {
        "question": "How do I update my mailing address?",
        "ground_truth": "You can update your address through online banking, mobile app, phone banking (1-800-555-BANK), or in-branch visits. For standard same-state changes, you need a valid government-issued photo ID and proof of new address dated within 60 days (utility bill, lease agreement, mortgage statement, or government correspondence). Processing takes 1-2 business days for online submissions.",
        "intent": "ADDRESS_UPDATE"
    },
    {
        "question": "What documents do I need for a same-state address change?",
        "ground_truth": "For a same-state address change, you need a valid government-issued photo ID (driver's license, passport, or state ID) and proof of new address dated within 60 days. Acceptable proof includes utility bills, lease agreements, mortgage statements, bank statements from another institution, or government correspondence from DMV or IRS.",
        "intent": "ADDRESS_UPDATE"
    },
    {
        "question": "How long does it take to process an address change through the mobile app?",
        "ground_truth": "Address updates through the mobile app take 1-2 business days to process. The mobile app provides self-service address updates through a secure portal with real-time validation of address format and instant confirmation upon submission.",
        "intent": "ADDRESS_UPDATE"
    },
    
    # Dispute Queries (from dispute_handling_policy.md)
    {
        "question": "I was charged twice for the same transaction. How do I dispute this?",
        "ground_truth": "Duplicate charges are a billing error type covered under the Fair Credit Billing Act. You have 60 days from the statement date to dispute billing errors. Submit your dispute through online banking, mobile app, phone banking, or in writing. Provide transaction details including dates, amounts, and merchant name. You'll receive provisional credit during investigation, and we'll respond within 10 business days.",
        "intent": "DISPUTE"
    },
    {
        "question": "What is my liability for unauthorized charges on my credit card?",
        "ground_truth": "Under the Fair Credit Billing Act, your maximum liability for unauthorized credit card charges is $50. If you report the unauthorized use before the card is used, you have zero liability. You have 60 days from the statement date to dispute charges.",
        "intent": "DISPUTE"
    },
    {
        "question": "How do I dispute a charge for goods I never received?",
        "ground_truth": "Goods not received is a merchant dispute type. Submit your dispute through online banking, mobile app, or phone banking. Provide order confirmation, tracking information, communication with merchant, and proof of non-delivery. Investigations typically take 30-45 days but can extend to 90 days for complex cases. You may receive provisional credit during the investigation.",
        "intent": "DISPUTE"
    },
    
    # Fraud Reporting Queries (from fraud_reporting_policy.md)
    {
        "question": "How do I report fraudulent charges on my account?",
        "ground_truth": "Report fraud immediately through the 24/7 fraud hotline (1-800-555-FRAUD), mobile app fraud alert button, online banking security center, or in-branch at any location. When reporting, provide your account number, list of suspicious transactions with dates and amounts, and last authorized transaction. Your account will be frozen immediately to prevent further unauthorized charges.",
        "intent": "FRAUD_REPORT"
    },
    {
        "question": "What happens after I report fraudulent activity?",
        "ground_truth": "After reporting fraud, we immediately freeze your account, cancel compromised cards, issue replacement cards via expedited shipping (2-3 business days), conduct a comprehensive account review, provide provisional credits for disputed amounts within 10 business days, and set up enhanced monitoring. You'll also receive identity theft protection resources if applicable.",
        "intent": "FRAUD_REPORT"
    },
    {
        "question": "Am I responsible for fraudulent charges made before I reported my card stolen?",
        "ground_truth": "Your liability depends on when you report. For credit cards: $0 if reported before use, $50 maximum if reported after unauthorized use. For debit cards: $0 if reported within 2 business days, $50 if reported within 60 days, potentially $500 or more if reported after 60 days. We typically provide zero-liability protection for prompt reporting.",
        "intent": "FRAUD_REPORT"
    },
    
    # Card Services Queries (from card_services_policy.md)
    {
        "question": "What should I do if my card is lost or stolen?",
        "ground_truth": "Immediately report lost or stolen cards through the 24/7 hotline (1-800-555-CARD), mobile app, or online banking. We'll cancel the card immediately, issue a replacement card (standard delivery 5-7 business days, expedited 2-3 business days), and monitor your account for unauthorized activity. You won't be liable for unauthorized charges made after you report the loss.",
        "intent": "CARD_SERVICES"
    },
    {
        "question": "Can I temporarily lock my card if I misplaced it?",
        "ground_truth": "Yes, you can temporarily lock your card instantly through the mobile app or online banking. This prevents all transactions while the card is locked. If you find your card, you can unlock it immediately through the same channels. If not found within 48 hours, request a permanent replacement.",
        "intent": "CARD_SERVICES"
    },
    
    # Payment Policy Queries (from payment_policy.md)
    {
        "question": "When is my payment due each month?",
        "ground_truth": "Your payment due date is shown on your monthly statement and remains the same each month. The minimum payment is due by 5:00 PM ET on the due date. Payments received after this time are considered late and may incur late fees. You can set up automatic payments or payment reminders to avoid missing payments.",
        "intent": "PAYMENT"
    },
    {
        "question": "How do I set up automatic payments?",
        "ground_truth": "Set up autopay through online banking or mobile app by navigating to Payment Settings and selecting AutoPay. Choose to pay the minimum payment, statement balance, or a fixed amount. Link your bank account using account and routing numbers. Autopay processes on your due date each month, and you'll receive confirmation 3 days before each payment.",
        "intent": "PAYMENT"
    },
    
    # Account Inquiry Queries (from account_inquiry_policy.md)
    {
        "question": "How do I check my account balance?",
        "ground_truth": "Check your balance through online banking, mobile app (real-time balance), phone banking (1-800-555-BANK automated system or representative), ATM, or monthly statements. Mobile app and online banking show real-time available balance and pending transactions. Phone banking and ATMs provide 24/7 access to balance information.",
        "intent": "ACCOUNT_INQUIRY"
    },
    {
        "question": "How far back can I view my transaction history?",
        "ground_truth": "Online banking and mobile app provide 18 months of transaction history. For records older than 18 months, request statements through customer service. Statements are available for up to 7 years. Download options include PDF, CSV, and QFX formats for financial software import.",
        "intent": "ACCOUNT_INQUIRY"
    }
]


def get_evaluation_dataset():
    """Return the evaluation dataset."""
    return EVALUATION_DATASET


if __name__ == "__main__":
    print(f"Evaluation dataset contains {len(EVALUATION_DATASET)} test queries")
    print("\nIntent distribution:")
    
    from collections import Counter
    intents = [item["intent"] for item in EVALUATION_DATASET]
    intent_counts = Counter(intents)
    
    for intent, count in intent_counts.items():
        print(f"  {intent}: {count}")
