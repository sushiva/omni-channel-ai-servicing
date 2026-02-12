async def send_notification_node(state):
    if not state.notify_client:
        return {}

    recipient = state.customer_email or "customer@example.com"
    await state.notify_client.send_email(
        to=recipient,
        subject="Your request is complete",
        body="We have processed your request."
    )
    return {}
