-- Detect gaps or tampering
SELECT 
    id,
    hash_chain = SHA256(hash_prev || timestamp || hash_data) AS valid_link
FROM entries
ORDER BY id;
