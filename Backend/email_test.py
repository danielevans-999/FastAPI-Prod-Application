
import smtplib

email = input("Enter sender email: ")
recipient = input("Enter recipient email: ")
subject = "Test Email from Python"
body = "This is a test email sent from a Python script."

server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login(email, "rzgveulvlrwjecwr")
try:
    server.sendmail(email, recipient, f"Subject: {subject}\n\n{body}")
    print("Email sent successfully!")
    
except Exception as e:
    print(f"Failed to send email: {e}")


