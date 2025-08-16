User(id, email, password_hash, display_name, avatar_url, created_at)
Group(id, name, description, owner_id, created_at)
Membership(id, user_id, group_id, created_at)
Message(id, user_id, group_id, content, created_at)