-- Create missing user record in users table
-- Replace the values below with your actual user ID and email from the error message

-- Your user ID from the error: 1746ebd6-3bd0-4664-b641-af43cef9059c
-- Replace 'your-email@example.com' with your actual email

INSERT INTO users (id, email, preferences, subscription_tier, created_at) 
VALUES (
    '1746ebd6-3bd0-4664-b641-af43cef9059c',  -- Replace with your user ID
    'your-email@example.com',                 -- Replace with your email
    '{"model_preference": "fast", "theme": "light"}',
    'free',
    NOW()
);

-- Verify the user was created
SELECT id, email, subscription_tier FROM users WHERE id = '1746ebd6-3bd0-4664-b641-af43cef9059c';