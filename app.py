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

        # Először listázzuk a mappákat (debug)
        status, folders = mail.list()
        
        # Spam keresése Gmail speciális keresővel
        mail.select('"[Gmail]/All Mail"')  # Összes levél mappa
        
        # Keresés a spam címkére
        status, messages = mail.search(None, 'X-GM-RAW', 'in:spam')
        
        if status != "OK" or not messages[0]:
            # Próbáljuk a sima Spam mappát is
            for folder in ['"[Gmail]/Spam"', "Spam"]:
                try:
                    mail.select(folder)
                    status, messages = mail.search(None, "ALL")
                    if status == "OK" and messages[0]:
                        break
                except:
                    continue

        if status != "OK" or not messages[0]:
            mail.logout()
            return jsonify({"success": True, "message": "Nem találtam több spamet."})

        msg_ids = messages[0].split()
        count = len(msg_ids)

        for num in msg_ids:
            try:
                # Áthelyezés Kukába
                mail.store(num, '+X-GM-LABELS', '\\Trash')
                mail.store(num, '+FLAGS', '\\Deleted')
            except Exception as e:
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
