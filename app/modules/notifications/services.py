import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_test_email(server, port, encryption, user, password, sender_name, sender_email, target_email):
    """
    Sends a test email to verify SMTP configuration.
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{sender_name} <{sender_email}>"
        msg['To'] = target_email
        msg['Subject'] = "⚡ Nexus Premium - SMTP Verification"

        body = f"""
        <html>
            <body style="font-family: sans-serif; color: #1a1a1a;">
                <h2 style="color: #6366f1;">⚡ Nexus System Verification</h2>
                <p>Usted está recibiendo este mensaje porque se ha solicitado una prueba de conectividad desde el panel de administración.</p>
                <div style="background: #f8fafc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0;">
                    <p><b>Status:</b> Conexión Exitosa</p>
                    <p><b>Servidor:</b> {server}:{port}</p>
                    <p><b>Cifrado:</b> {encryption.upper()}</p>
                </div>
                <p style="font-size: 11px; color: #64748b; margin-top: 20px;">
                    Este es un correo automático generado por Nexus Premium. Por favor no responda.
                </p>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        # Connect and Send
        if encryption == 'ssl':
            smtp = smtplib.SMTP_SSL(server, port, timeout=10)
        else:
            smtp = smtplib.SMTP(server, port, timeout=10)
            if encryption == 'starttls':
                smtp.starttls()

        if user and password:
            smtp.login(user, password)

        smtp.send_message(msg)
        smtp.quit()
        
        return {"status": "success", "message": "Correo de prueba enviado correctamente"}

    except Exception as e:
        return {"status": "error", "message": str(e)}
