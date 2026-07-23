from flask import Flask, render_template, request, jsonify
import imaplib

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

        # Próbáljuk megtalálni a Spam mappát
        status, folders = mail.list()
        spam_folder = None

        for folder in folders:
            folder_name = folder.decode()
            if "Spam" in folder_name or "Spam" in folder_name:
                # Kinyerjük a mappa nevét
                parts = folder_name.split(' "/" ')
                if len(parts) > 1:
                    spam_folder = parts[-1].strip('"')
                    break

        if not spam_folder:
            # Fallback
            spam_folder = "[Gmail]/Spam"

        status, _ = mail.select(f'"{spam_folder}"')
        if status != "OK":
            # Próbáljuk idézőjelek nélkül
            status, _ = mail.select(spam_folder)

        if status != "OK":
            mail.logout()
            return jsonify({"success": False, "message": f"Nem sikerült megnyitni a Spam mappát: {spam_folder}"})

        status, messages = mail.search(None, "ALL")

        if status != "OK" or not messages[0]:
            mail.logout()
            return jsonify({"success": True, "message": "A Spam mappa üres."})

        msg_ids = messages[0].split()
        count = len(msg_ids)

        for num in msg_ids:
            try:
                mail.store(num, '+X-GM-LABELS', '\\Trash')
                mail.store(num, '+FLAGS', '\\Deleted')
            except:
                pass

        mail.expunge()
        mail.logout()

        return jsonify({
            "success": True,
            "message": f"Kész! {count} darab spam a Kukába került."
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Hiba: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)
