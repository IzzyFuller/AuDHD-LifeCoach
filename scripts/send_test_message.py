#!/usr/bin/env python
"""
A simple script to send a test message to the RabbitMQ queue.
This can be used to test the message consumer functionality.
"""
import json
import pika
import sys
import datetime

# RabbitMQ connection parameters
host = "localhost"  # Change this if RabbitMQ is running elsewhere
port = 5672
username = "guest"
password = "guest"
queue_name = "communications"

# Sample message data
default_message = {
    "content": "I need to meet with the team tomorrow at 2pm to discuss the project timeline.",
    "sender": "user@example.com",
    "recipient": "assistant@example.com",
    "timestamp": datetime.datetime.now().isoformat()
}

def send_message(message_data=None):
    """
    Send a message to the RabbitMQ queue.
    
    Args:
        message_data: The message data to send. If None, a default message will be used.
    """
    message_data = message_data or default_message
    
    # Connect to RabbitMQ
    credentials = pika.PlainCredentials(username, password)
    parameters = pika.ConnectionParameters(
        host=host,
        port=port,
        credentials=credentials
    )
    
    try:
        # Establish connection
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Ensure queue exists
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Convert message to JSON
        message_body = json.dumps(message_data)
        
        # Publish message
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=message_body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type='application/json'
            )
        )
        
        print(f"✅ Message sent successfully to queue '{queue_name}'")
        print(f"Message content: {message_body}")
        
        # Close connection
        connection.close()
        
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Check if message content is provided as command-line argument
    if len(sys.argv) > 1:
        content = " ".join(sys.argv[1:])
        custom_message = default_message.copy()
        custom_message["content"] = content
        send_message(custom_message)
    else:
        send_message()