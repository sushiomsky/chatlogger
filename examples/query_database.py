"""Example script demonstrating how to query the database."""

from src.database import ChatDatabase


def main():
    """Query and display messages from the database."""
    db_path = 'chat_logs.db'
    
    with ChatDatabase(db_path) as db:
        # Get total message count
        total = db.get_message_count()
        print(f"Total messages in database: {total}")
        
        if total > 0:
            print("\n--- Last 10 messages ---")
            messages = db.get_messages(limit=10)
            for msg in messages:
                print(f"[{msg['timestamp']}] {msg['username']}: {msg['message']}")
            
            print("\n--- Most active users (sample) ---")
            # Get all messages and count by user
            all_messages = db.get_messages(limit=1000)
            user_counts = {}
            for msg in all_messages:
                username = msg['username']
                user_counts[username] = user_counts.get(username, 0) + 1
            
            # Sort by count
            top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for username, count in top_users:
                print(f"{username}: {count} messages")
        else:
            print("No messages in database yet.")


if __name__ == '__main__':
    main()
