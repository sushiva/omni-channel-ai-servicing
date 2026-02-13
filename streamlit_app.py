"""
Streamlit UI for Omni-Channel AI Servicing Demo

Interactive demo showcasing real-time RAG-powered customer service workflows.
Users can ask banking questions and see the full workflow execution.
"""
import streamlit as st
import requests
import json
import time
from typing import Dict, Any, Optional

# Page configuration
st.set_page_config(
    page_title="AI Banking Assistant Demo",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_BASE_URL = "http://localhost:8000"  # Will be updated for HuggingFace deployment

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


def check_api_health() -> bool:
    """Check if the backend API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def call_service_api(message: str, customer_id: str = "DEMO_USER", channel: str = "web", metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Call the /api/v1/service-request API endpoint"""
    try:
        # Build metadata
        base_metadata = {
            "source": "streamlit_demo",
            "timestamp": time.time()
        }
        
        # Merge with provided metadata
        if metadata:
            base_metadata.update(metadata)
        
        payload = {
            "message": message,
            "customer_id": customer_id,
            "channel": channel,
            "metadata": base_metadata
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/service-request",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("Request timed out. The API might be processing a complex query.")
        return None
    except Exception as e:
        st.error(f"Error calling API: {str(e)}")
        return None


def display_workflow_result(result: Dict[str, Any]):
    """Display the workflow execution result with rich formatting"""
    
    # Main response
    st.markdown("### 🤖 AI Response")
    st.markdown(f'<div class="success-box">{result.get("response", "No response")}</div>', unsafe_allow_html=True)
    
    # Create columns for metadata
    col1, col2, col3 = st.columns(3)
    
    with col1:
        intent = result.get("intent", "unknown")
        st.metric("Intent Classified", intent.replace("_", " ").title())
    
    with col2:
        workflow = result.get("workflow", "unknown")
        st.metric("Workflow Used", workflow.replace("_", " ").title())
    
    with col3:
        status = result.get("status", "unknown")
        status_emoji = "✅" if status == "success" else "⚠️"
        st.metric("Status", f"{status_emoji} {status.title()}")
    
    # Detailed workflow result
    with st.expander("📊 View Detailed Workflow Execution"):
        workflow_result = result.get("result", {})
        st.json(workflow_result)
    
    # Request metadata
    with st.expander("🔍 View Request Metadata"):
        metadata = {
            "Request ID": result.get("request_id", "unknown"),
            "Intent": result.get("intent", "unknown"),
            "Workflow": result.get("workflow", "unknown"),
            "Status": result.get("status", "unknown")
        }
        st.json(metadata)


def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<div class="main-header">🏦 AI Banking Assistant Demo</div>', unsafe_allow_html=True)
    st.markdown("Experience real-time RAG-powered customer service workflows")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📚 About This Demo")
        st.markdown("""
        This demo showcases an **enterprise-grade RAG system** for banking customer service.
        
        **Key Features:**
        - 🧠 Intent classification
        - 📖 Knowledge base retrieval (523 chunks)
        - 🔄 Specialized workflows
        - 📊 Real-time policy enforcement
        - ✅ RAGAS-validated responses
        
        **Tech Stack:**
        - LangGraph workflows
        - FAISS vector store
        - OpenAI embeddings
        - GPT-4o-mini generation
        """)
        
        st.markdown("---")
        
        st.markdown("### ⚙️ Configuration")
        customer_id = st.text_input("Customer ID", value="DEMO_USER")
        channel = st.selectbox("Channel", ["web", "chat", "mobile", "email"], index=0)
        
        st.markdown("---")
        
        # API Health Check
        st.markdown("### 🔌 API Status")
        if st.button("Check Backend Health"):
            with st.spinner("Checking..."):
                if check_api_health():
                    st.success("✅ Backend API is healthy")
                else:
                    st.error("❌ Backend API is not responding")
                    st.info("Make sure the FastAPI server is running on port 8000")
        
        st.markdown("---")
        
        # Example queries
        st.markdown("### 💡 Example Queries")
        example_queries = [
            "How do I update my mailing address?",
            "I want to dispute a charge on my account",
            "Someone used my card without permission",
            "What are your hours of operation?",
            "How do I activate my new credit card?",
            "I need to report fraudulent activity"
        ]
        
        for query in example_queries:
            if st.button(query, key=f"example_{query[:20]}"):
                st.session_state["user_input"] = query
    
    # Main content area - Tabs for different interaction modes
    tab1, tab2 = st.tabs(["💬 Chat Interface", "📧 Email Simulation"])
    
    # Initialize session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "email_inbox" not in st.session_state:
        st.session_state.email_inbox = []
    
    # Tab 1: Chat Interface (existing functionality)
    with tab1:
        st.markdown("### 💬 Ask a Question")
    
    # User input
    user_input = st.text_area(
        "Enter your question:",
        value=st.session_state.get("user_input", ""),
        height=100,
        placeholder="e.g., How do I update my address?",
        key="main_input"
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        submit_button = st.button("🚀 Submit", type="primary")
    with col2:
        clear_button = st.button("🗑️ Clear History")
    
    if clear_button:
        st.session_state.chat_history = []
        st.session_state["user_input"] = ""
        st.rerun()
    
    # Process query
    if submit_button and user_input.strip():
        with st.spinner("🔄 Processing your request..."):
            start_time = time.time()
            
            # Call API
            result = call_service_api(
                message=user_input,
                customer_id=customer_id,
                channel=channel
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if result:
                # Add to chat history
                st.session_state.chat_history.append({
                    "query": user_input,
                    "result": result,
                    "processing_time": processing_time
                })
                
                # Display result
                st.markdown("---")
                st.markdown(f"⏱️ **Processing Time:** {processing_time:.2f}s")
                display_workflow_result(result)
                
                # Clear input
                st.session_state["user_input"] = ""
    
        # Display chat history
        if st.session_state.chat_history:
            st.markdown("---")
            st.markdown("### 📜 Conversation History")
            
            for idx, item in enumerate(reversed(st.session_state.chat_history)):
                with st.expander(f"Query {len(st.session_state.chat_history) - idx}: {item['query'][:50]}..."):
                    st.markdown(f"**Query:** {item['query']}")
                    st.markdown(f"**Processing Time:** {item['processing_time']:.2f}s")
                    display_workflow_result(item['result'])
    
    # Tab 2: Email Simulation
    with tab2:
        st.markdown("### 📧 Email Support Simulation")
        st.markdown("""
        Simulate sending an email to **support@demobank.ai** and receive an automated response.
        This demonstrates the email channel with document verification workflow.
        """)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### ✉️ Compose Email")
            
            # User email input
            col_email, col_name = st.columns(2)
            with col_email:
                email_from = st.text_input("Your Email:", value="jane.doe@example.com", key="email_from")
            with col_name:
                user_name = st.text_input("Your Name:", value="Jane Doe", key="user_name")
            
            email_subject = st.text_input("Subject:", value="Address Update Request", key="email_subject")
            
            email_body = st.text_area(
                "Message:",
                value="""Hi,

I recently moved and need to update my mailing address.

My new address is:
456 Oak Avenue, Apt 2B
Austin, TX 78701

I have attached my driver's license and a recent utility bill as proof of my new address.

Please let me know if you need anything else.

Thank you,
Jane Doe""",
                height=300,
                key="email_body"
            )
            
            st.markdown("**Attachments:**")
            col_a, col_b = st.columns(2)
            with col_a:
                has_id = st.checkbox("📄 drivers_license.pdf", value=True, key="attach_id")
            with col_b:
                has_proof = st.checkbox("📄 utility_bill.pdf", value=True, key="attach_proof")
            
            if st.button("📤 Send Email", type="primary", key="send_email"):
                with st.spinner("📨 Sending email and processing..."):
                    start_time = time.time()
                    
                    # Build metadata
                    metadata = {
                        "email_sender": email_from,
                        "email_subject": email_subject,
                        "email_message_id": f"<{int(time.time())}@example.com>",
                        "has_attachments": has_id or has_proof,
                        "attachments": [],
                        "customer_name": user_name  # Add customer name for personalization
                    }
                    
                    if has_id:
                        metadata["attachments"].append("drivers_license.pdf")
                    if has_proof:
                        metadata["attachments"].append("utility_bill.pdf")
                    
                    # Call API with email channel
                    result = call_service_api(
                        message=email_body,
                        customer_id=email_from,
                        channel="email",
                        metadata=metadata
                    )
                    
                    end_time = time.time()
                    processing_time = end_time - start_time
                    
                    if result:
                        # Add to inbox
                        email_response = {
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "from": email_from,
                            "user_name": user_name,
                            "subject": email_subject,
                            "original_message": email_body,
                            "attachments": metadata["attachments"],
                            "response": result,
                            "processing_time": processing_time
                        }
                        st.session_state.email_inbox.insert(0, email_response)
                        
                        st.success("✅ Email sent and processed successfully!")
                        st.rerun()
        
        with col2:
            st.markdown("#### 📬 Your Inbox")
            # Show current user's email if they've sent anything
            if st.session_state.email_inbox:
                current_email = st.session_state.email_inbox[0]['from']
                st.markdown(f"**{current_email}**")
            else:
                st.markdown("**Your Email Address**")
            st.markdown(f"**Messages:** {len(st.session_state.email_inbox)}")
            st.markdown("---")
            st.markdown("📧 **To:** support@demobank.ai")
            
            if st.button("🗑️ Clear Inbox", key="clear_inbox"):
                st.session_state.email_inbox = []
                st.rerun()
        
        # Display email responses
        if st.session_state.email_inbox:
            st.markdown("---")
            st.markdown("### 📥 Your Inbox - Responses from support@demobank.ai")
            
            for idx, email in enumerate(st.session_state.email_inbox):
                with st.expander(f"📧 {email['timestamp']} - Re: {email['subject']}", expanded=(idx == 0)):
                    st.markdown(f"**To:** {email.get('user_name', 'Customer')} ({email['from']})")
                    st.markdown(f"**From:** support@demobank.ai")
                    st.markdown(f"**Subject:** Re: {email['subject']}")
                    st.markdown(f"**Received:** {email['timestamp']}")
                    
                    st.markdown("---")
                    st.markdown("**📨 Your Original Message:**")
                    with st.container():
                        st.text(email['original_message'][:200] + "..." if len(email['original_message']) > 200 else email['original_message'])
                        if email['attachments']:
                            st.markdown(f"📎 **Attachments:** {', '.join(email['attachments'])}")
                    
                    st.markdown("---")
                    st.markdown("**✉️ Response from Customer Support:**")
                    st.markdown(f"⏱️ **Processing Time:** {email['processing_time']:.2f}s")
                    
                    display_workflow_result(email['response'])
        else:
            st.info("📭 No emails in inbox yet. Send an email above to see the automated response.")

    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p><strong>Omni-Channel AI Servicing Platform</strong></p>
        <p>Built with LangGraph • FAISS • OpenAI • Streamlit</p>
        <p>🔒 Demo Mode - No real transactions processed</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
