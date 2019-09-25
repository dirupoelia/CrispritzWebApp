# import for send mail
import sys
import smtplib
from email.message import EmailMessage
import ssl

with open (sys.argv[1] + '/email.txt', 'r') as e:
    #message building
    msg = EmailMessage()
    msg['to'] = e.readline().strip()
    
    msg['Subject'] = 'Job ... Done'

    msg['From'] = "elia.dirupo@hotmail.it"
    content_email = 'Job done, visit link ' + e.readline().strip() + ' to view. ' + e.readline()
    msg.set_content(content_email)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS)

    print('Prima smtp_ssl')
    server = smtplib.SMTP('smtp-mail.outlook.com', 587)

    #server = smtplib.SMTP_SSL("smtp.live.com",587)
    #for example:
    #server = smtplib.SMTP_SSL("smtp.libero.it", port=465)
    print('Prima ehlo')
    #start connection
    server.ehlo()
    server.starttls(context=context)
    server.ehlo()
    #login and send message
    print('Prima login')
    server.login("elia.dirupo@hotmail.it", "--set_password--")
    print('Prima send_message')
    server.send_message(msg)
    print('Prima quit')
    #close connection
    server.quit()
