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

        total_moved = 0

        # 1. módszer: közvetlen Spam mappa
        possible_spam = ['"[Gmail]/Spam"', "[Gmail]/Spam", "Spam", '"Spam"']
        
        for folder in possible_spam:
            try:
                status, _ = mail.select(folder)
                if status == "OK":
                    status, messages = mail.search(None, "ALL")
                    if status == "OK" and messages[0]:
                        msg_ids = messages[0].split()
                        for num in msg_ids:
                            try:
                                mail.store(num, '+X-GM-LABELS', '\\Trash')
                                mail.store(num, '+FLAGS', '\\Deleted')
                                total_moved += 1
                            except:
                                pass
                        mail.expunge()
            except:
                continue

        # 2. módszer: All Mail + in:spam keresés
        try:
            mail.select('"[Gmail]/All Mail"')
            status, messages = mail.search(None, 'X-GM-RAW', 'in:spam')
            if status == "OK" and messages[0]:
                msg_ids = messages[0].split()
                for num in msg_ids:
                    try:
                        mail.store(num, '+X-GM-LABELS', '\\Trash')
                        mail.store(num, '+FLAGS', '\\Deleted')
                        total_moved += 1
                    except:
                        pass
                mail.expunge()
        except:
            pass

        mail.logout()

        if total_moved == 0:
            return jsonify({"success": True, "message": "Nem találtam több spamet."})
        else:
            return jsonify({
                "success": True,
                "message": f"Kész! {total_moved} darab spam a Kukába került."
            })

    except Exception as e:
        return jsonify({"success": False, "message": f"Hiba: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)
