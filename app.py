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

        # 1. Klasszikus Spam
        for folder in ['"[Gmail]/Spam"', "[Gmail]/Spam", "Spam"]:
            try:
                status, _ = mail.select(folder)
                if status == "OK":
                    status, data = mail.uid('search', None, "ALL")
                    if status == "OK" and data[0]:
                        for uid in data[0].split():
                            try:
                                mail.uid('COPY', uid, '[Gmail]/Trash')
                                mail.uid('STORE', uid, '+FLAGS', '\\Deleted')
                                total_moved += 1
                            except:
                                pass
                        mail.expunge()
                    break
            except:
                continue

        # 2. Social + Promotions kategóriák (All Mail-ből)
        try:
            mail.select('"[Gmail]/All Mail"')
            
            # Social
            status, data = mail.uid('search', None, 'X-GM-RAW', 'category:social')
            if status == "OK" and data[0]:
                for uid in data[0].split():
                    try:
                        mail.uid('COPY', uid, '[Gmail]/Trash')
                        mail.uid('STORE', uid, '+FLAGS', '\\Deleted')
                        total_moved += 1
                    except:
                        pass

            # Promotions
            status, data = mail.uid('search', None, 'X-GM-RAW', 'category:promotions')
            if status == "OK" and data[0]:
                for uid in data[0].split():
                    try:
                        mail.uid('COPY', uid, '[Gmail]/Trash')
                        mail.uid('STORE', uid, '+FLAGS', '\\Deleted')
                        total_moved += 1
                    except:
                        pass

            mail.expunge()
        except:
            pass

        mail.logout()

        if total_moved == 0:
            return jsonify({"success": True, "message": "Nem találtam több törlendő levelet."})
        else:
            return jsonify({
                "success": True,
                "message": f"Kész! {total_moved} darab levél a Kukába került."
            })

    except Exception as e:
        return jsonify({"success": False, "message": f"Hiba: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)
