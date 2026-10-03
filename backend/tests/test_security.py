import hashlib

from app.core.security import (
    generate_token,
    hash_password,
    hash_token,
    password_needs_rehash,
    tokens_match,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_uses_argon2id_format(self) -> None:
        assert hash_password("correct horse battery staple").startswith("$argon2id$")

    def test_verification_succeeds_for_correct_password(self) -> None:
        stored = hash_password("s3cret-Password!")
        assert verify_password("s3cret-Password!", stored) is True

    def test_verification_fails_for_wrong_password(self) -> None:
        stored = hash_password("s3cret-Password!")
        assert verify_password("wrong-password", stored) is False

    def test_verification_fails_for_malformed_hash_without_raising(self) -> None:
        assert verify_password("anything", "not-a-valid-hash") is False

    def test_salting_produces_unique_hashes(self) -> None:
        assert hash_password("same") != hash_password("same")

    def test_hash_never_contains_the_password(self) -> None:
        secret = "visible-in-logs-would-be-bad"
        assert secret not in hash_password(secret)

    def test_fresh_hash_does_not_need_rehash(self) -> None:
        assert password_needs_rehash(hash_password("whatever")) is False


class TestTokenGeneration:
    def test_tokens_are_unique(self) -> None:
        assert generate_token() != generate_token()

    def test_tokens_carry_256_bits_of_entropy(self) -> None:
        # 32 random bytes -> 43 URL-safe base64 characters (no padding).
        assert len(generate_token()) == 43

    def test_tokens_are_url_safe(self) -> None:
        token = generate_token()
        assert token.replace("-", "").replace("_", "").isalnum()


class TestTokenHashing:
    def test_hash_is_deterministic(self) -> None:
        token = generate_token()
        assert hash_token(token) == hash_token(token)

    def test_hash_matches_known_sha256_value(self) -> None:
        assert hash_token("test-token") == hashlib.sha256(b"test-token").hexdigest()

    def test_hash_is_64_hex_characters(self) -> None:
        assert len(hash_token(generate_token())) == 64

    def test_match_roundtrip(self) -> None:
        token = generate_token()
        stored = hash_token(token)
        assert tokens_match(token, stored) is True
        assert tokens_match("forged-token", stored) is False
