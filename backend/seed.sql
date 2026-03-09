-- Direct SQL to seed user into database
-- Hash generated for password: qapassword12

-- First, ensure the users table exists
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Delete if exists and recreate (use DELETE if exists instead)
DELETE FROM users WHERE email = 'qa_user@datapulse.com';

-- Insert the user with pre-hashed password for qapassword12
-- bcrypt hash: $2b$12$S8HbvElT9.4.aVV3vVCbQexzWXPrFrQkVEVPmMVKkfmEe5f6pRWJu
INSERT INTO users (email, hashed_password, full_name, is_active, created_at) 
VALUES (
    'qa_user@datapulse.com',
    '$2b$12$S8HbvElT9.4.aVV3vVCbQexzWXPrFrQkVEVPmMVKkfmEe5f6pRWJu',
    'Tob',
    TRUE,
    NOW()
);

-- Verify insertion
SELECT id, email, full_name, is_active, created_at FROM users WHERE email = 'qa_user@datapulse.com';
