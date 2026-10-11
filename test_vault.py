"""Unit tests for the vault - run with:  python test_vault.py"""
import json, os, tempfile, unittest
from vault import Vault, VaultError, check_strength, generate_password


class VaultTests(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "v.dat")

    def test_create_unlock_roundtrip(self):
        v = Vault(self.path); v.create("Master#Pass123")
        v.add("github.com", "janice", "S3cret!pw")
        w = Vault(self.path); w.unlock("Master#Pass123")
        self.assertEqual(w.entries[0]["password"], "S3cret!pw")

    def test_wrong_password_rejected(self):
        Vault(self.path).create("Master#Pass123")
        with self.assertRaises(VaultError):
            Vault(self.path).unlock("wrong-password")

    def test_file_is_encrypted(self):
        v = Vault(self.path); v.create("Master#Pass123")
        v.add("bank.com", "janice", "PlainTextCheck99")
        raw = open(self.path).read()
        self.assertNotIn("PlainTextCheck99", raw)
        self.assertNotIn("bank.com", raw)

    def test_tamper_detection(self):
        v = Vault(self.path); v.create("Master#Pass123")
        blob = json.load(open(self.path)); blob["data"] = "A" + blob["data"][1:]
        json.dump(blob, open(self.path, "w"))
        with self.assertRaises(VaultError):
            Vault(self.path).unlock("Master#Pass123")

    def test_update_delete_search(self):
        v = Vault(self.path); v.create("Master#Pass123")
        e = v.add("mail.com", "a", "p1"); v.update(e["id"], password="p2")
        self.assertEqual(v.get(e["id"])["password"], "p2")
        self.assertEqual(len(v.search("mail")), 1)
        v.delete(e["id"]); self.assertEqual(v.entries, [])

    def test_generator(self):
        pw = generate_password(20)
        self.assertEqual(len(pw), 20)
        self.assertTrue(any(c.isupper() for c in pw) and any(c.isdigit() for c in pw))
        self.assertNotEqual(generate_password(20), generate_password(20))

    def test_strength(self):
        self.assertEqual(check_strength("password")[0], 0)
        self.assertLess(check_strength("abc")[0], 2)
        self.assertEqual(check_strength("Xk9#mQ2$vL7!pR4&zT")[0], 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
