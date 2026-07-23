from flask import Flask, render_template, request, jsonify
import imaplib
import os

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/clean", methods=["POST"])
def clean():
    data = request.json
    email_addr = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not email_addr or not password:
        return jsonify({"success": False, "message": "Email és jelszó megadása kötelező."})

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_addr, password)

        # Spam mappa
        status, _ = mail.select('"[Gmail]/Spam"')
        if status != "OK":
            # Próbáljuk az angol nevet is
            mail.select("Spam")

        status, messages = mail.search(None, "ALL")
        
        if status != "OK" or not messages[0]:
            mail.logout()
            return jsonify({"success": True, "message": "A Spam mappa üres."})

        msg_ids = messages[0].split()
        count = len(msg_ids)

        for num in msg_ids:
            mail.store(num, '+X-GM-LABELS', '\\Trash')
            mail.store(num, '+FLAGS', '\\Deleted')

        mail.expunge()
        mail.logout()

        return jsonify({
            "success": True,
            "message": f"Kész! {count} darab spam a Kukába került."
        })

    except imaplib.IMAP4.error as e:
        return jsonify({"success": False, "message": f"Bejelentkezési hiba: {str(e)}"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Hiba: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)