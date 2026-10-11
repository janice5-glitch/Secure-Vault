# 🔐 SecureVault - Secure Password Manager

A locally hosted password manager built with **Python (Flask)** that protects all your credentials behind a single master password using **AES-256-GCM** encryption and **PBKDF2** key derivation.

> Mini Project - B.Tech Information Technology, St. Joseph's Institute of Technology, Chennai

---

## ✨ Features

- **Master password vault** - remember one password, everything else is encrypted
- **AES-256-GCM encryption** - confidentiality plus tamper detection for the vault file
- **PBKDF2-HMAC-SHA256** key derivation (600,000 iterations, random 16-byte salt)
- **Credential management** - add, edit, delete and search entries
- **Secure password generator** - uses Python's `secrets` (CSPRNG); choose length, uppercase, digits, symbols
- **Live strength meter** - entropy-based rating (Very Weak → Very Strong) with improvement tips
- **Weak password detection** - dashboard shows how many saved passwords need attention
- **Auto-lock** after 5 minutes of inactivity and manual lock
- **Brute-force protection** - 60-second lock-out after 5 wrong master-password attempts
- **Offline & private** - no cloud, no third party; data stays in one local file
- Show/hide and copy buttons (clipboard cleared after 20 seconds)

## 🖼️ Screenshots

| Create vault | Dashboard |
|---|---|
| ![Setup](screenshots/01_setup.png) | ![Dashboard](screenshots/04_dashboard.png) |

| Password generator | Encrypted `vault.dat` |
|---|---|
| ![Generator](screenshots/07_generator.png) | ![Encrypted file](screenshots/10_encrypted_vault.png) |

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.9+ |
| Web framework | Flask 3 |
| Cryptography | `cryptography` (AES-GCM, PBKDF2HMAC) |
| Front end | HTML5, CSS3, JavaScript (Fetch API) |
| Testing | `unittest` |

## 🚀 Getting Started

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/SecureVault.git
cd SecureVault

# 2. (Optional) create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Open **http://127.0.0.1:5000** in your browser. On first run you will be asked to create a master password - this creates `vault.dat`.

> ⚠️ There is **no password recovery**. If you forget the master password, the vault cannot be decrypted.

## 🧪 Run the Tests

```bash
python test_vault.py
```

The 7 tests cover: encrypt/decrypt round-trip, wrong-password rejection, file really encrypted, tamper detection, add/update/delete/search, password generator and strength checker.

## 📁 Project Structure

```
SecureVault/
├── app.py              # Flask web app (routes, session, auto-lock, lock-out)
├── vault.py            # Crypto core (PBKDF2, AES-256-GCM, generator, strength)
├── test_vault.py       # Unit tests
├── requirements.txt
├── templates/          # login, dashboard, add/edit, generator pages
├── static/style.css
└── screenshots/
```

## 🔒 How It Works

```
Master Password ──► PBKDF2-HMAC-SHA256 (salt, 600k iterations) ──► 256-bit key
                                                                      │
vault.dat  { salt | nonce | ciphertext }  ──► AES-256-GCM decrypt ◄───┘
                                                 │ tag mismatch → "Incorrect master password"
                                                 ▼
                    in-memory entries ──► add / edit / delete / search
                                                 │
                    every change ──► new random nonce ──► encrypt ──► save vault.dat
```

- The master password and key are **never written to disk**.
- A fresh random nonce is used on every save.
- Any modification of `vault.dat` makes decryption fail (GCM authentication tag).

## ⚠️ Limitations

This is an educational mini project. It is designed for single-user, local use (`127.0.0.1`) - do not expose it to the internet. Not independently security audited.

## 🔮 Future Enhancements

- Two-factor authentication (TOTP) for unlock
- Browser extension with auto-fill
- Encrypted cloud backup / multi-device sync
- Breach checker (Have I Been Pwned k-anonymity API)
- Argon2id key derivation
- Encrypted import / export, password expiry reminders

## 👩‍💻 Author

**Janice A.R** - B.Tech Information Technology, St. Joseph's Institute of Technology

## 📄 License

Released under the MIT License.
