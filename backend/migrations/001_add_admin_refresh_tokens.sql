ALTER TABLE refresh_tokens
    ALTER COLUMN user_id DROP NOT NULL;

ALTER TABLE refresh_tokens
    ADD COLUMN admin_id INTEGER;

ALTER TABLE refresh_tokens
    ADD CONSTRAINT refresh_tokens_admin_id_fkey
    FOREIGN KEY (admin_id) REFERENCES admindata(admin_id);