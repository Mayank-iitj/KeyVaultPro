"""
Security Tests
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

import pytest
from app.security.hashing import hashing_service
from app.security.encryption import EncryptionService
from app.security.key_generator import key_generator


class TestHashing:
    def test_password_hashing(self):
        password = "SecurePassword123!"
        hashed = hashing_service.hash_password(password)
        
        assert hashed != password
        assert hashing_service.verify_password(password, hashed) is True
        assert hashing_service.verify_password("wrong", hashed) is False
    
    def test_api_key_hashing(self):
        api_key = "akm_test123456789"
        hashed = hashing_service.hash_api_key(api_key)
        
        assert hashed != api_key
        assert len(hashed) == 64
        assert hashing_service.hash_api_key(api_key) == hashed
    
    def test_token_hashing(self):
        token = "some_random_token_value"
        hashed = hashing_service.hash_token(token)
        
        assert hashed != token
        assert len(hashed) == 64


class TestEncryption:
    def test_encrypt_decrypt(self):
        encryption = EncryptionService("test_master_key_12345")
        plaintext = "sensitive data"
        
        encrypted = encryption.encrypt(plaintext)
        decrypted = encryption.decrypt(encrypted)
        
        assert encrypted != plaintext
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_dict(self):
        encryption = EncryptionService("test_master_key_12345")
        data = {"key": "value", "nested": {"a": 1}}
        
        encrypted = encryption.encrypt_dict(data)
        decrypted = encryption.decrypt_dict(encrypted)
        
        assert encrypted != str(data)
        assert decrypted == data
    
    def test_empty_string(self):
        encryption = EncryptionService("test_master_key_12345")
        
        assert encryption.encrypt("") == ""
        assert encryption.decrypt("") == ""


class TestKeyGenerator:
    def test_generate_api_key(self):
        api_key, prefix = key_generator.generate_api_key()
        
        assert api_key.startswith("akm_")
        assert prefix == api_key[:8]
        assert len(api_key) > 30
    
    def test_generate_api_key_custom_prefix(self):
        api_key, prefix = key_generator.generate_api_key("custom")
        
        assert api_key.startswith("custom_")
    
    def test_generate_refresh_token(self):
        token = key_generator.generate_refresh_token()
        
        assert len(token) > 50
    
    def test_generate_secret(self):
        secret = key_generator.generate_secret(32)
        
        assert len(secret) == 32
        assert secret.isalnum()
    
    def test_is_valid_key_format(self):
        valid_key = "akm_" + "a" * 30
        invalid_key1 = "invalid"
        invalid_key2 = "akm_short"
        invalid_key3 = ""
        
        assert key_generator.is_valid_key_format(valid_key) is True
        assert key_generator.is_valid_key_format(invalid_key1) is False
        assert key_generator.is_valid_key_format(invalid_key2) is False
        assert key_generator.is_valid_key_format(invalid_key3) is False
    
    def test_unique_keys(self):
        keys = [key_generator.generate_api_key()[0] for _ in range(100)]
        
        assert len(set(keys)) == 100
