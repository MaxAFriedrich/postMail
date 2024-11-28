import re
import smtplib
import urllib.parse
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
import yaml


@dataclass
class SubmissionPoint:
    submission_url: str
    success_url: str
    error_url: str
    subject: str
    to_email: str

    @classmethod
    def from_dict(cls, data):
        return cls(
            submission_url=data['submission_url'],
            success_url=data['success_url'],
            error_url=data['error_url'],
            subject=data['subject'],
            to_email=data['to_email']
        )


@dataclass
class Config:
    sender_email: str
    sender_login: str
    sender_password: str
    smtp_server: str
    smtp_port: int
    turnstile_secret: str
    submission_points: list[SubmissionPoint]

    @classmethod
    def from_dict(cls, data):
        return cls(
            sender_email=data['sender_email'],
            sender_login=data['sender_login'],
            sender_password=data['sender_password'],
            smtp_server=data['smtp_server'],
            smtp_port=data['smtp_port'],
            turnstile_secret=data['turnstile_secret'],
            submission_points=[SubmissionPoint.from_dict(point) for point in
                               data['submission_points']]
        )


config = Config.from_dict(
    yaml.load(open('config.yml', 'r'), Loader=yaml.FullLoader))


def valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if re.match(regex, email):
        return True
    return False


def build_content(form_data):
    content = ''
    for key, value in form_data.items():
        if key == 'cf-turnstile-response':
            continue
        content += f"**{key}**\n{''.join(value)}\n---------\n"
    return content


def send_email(email, subject, content, reply_to=None):
    print(f"Sending email to {email} with subject: {subject}")
    return
    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = config.sender_email
    msg['To'] = email
    if reply_to:
        msg['Reply-To'] = reply_to
    msg['Subject'] = subject

    # Attach the email content
    msg.attach(MIMEText(content, 'plain'))

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP(config.smtp_server, config.smtp_port)
        server.starttls()
        server.login(config.sender_login, config.sender_password)

        # Send the email
        server.sendmail(config.sender_email, email, msg.as_string())

        server.quit()
        return True
    except Exception as e:
        print(e)
        return False


def route_validation(path):
    for point in config.submission_points:
        if point.submission_url == path:
            return point
    return None


def turnstile_validation(token, ip):
    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    payload = {
        'secret': config.turnstile_secret,
        'response': token,
        'remoteip': ip
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=payload, headers=headers)
    outcome = response.json()
    print(outcome)
    return outcome.get('success', False)


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'404 Not Found')

    def do_POST(self):
        if (point := route_validation(self.path)) is not None:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            form_data = urllib.parse.parse_qs(post_data.decode('utf-8'))

            cf_ip = self.headers.get('CF-Connecting-IP', '')
            token = form_data.get('cf-turnstile-response', [''])[0]
            print(f"Received POST request from {cf_ip} with token {token[:5]}")

            if not turnstile_validation(token, cf_ip):
                print(f"Turnstile validation failed for {cf_ip}")
                self.send_response(302)
                self.send_header('Location', point.error_url)
                return

            email = "".join(form_data.get('email', ['']))
            content = build_content(form_data)

            result = False
            if valid_email(email) and len(content) > 0:
                result = send_email(point.to_email, point.subject, content,
                                    email)

            self.send_response(302)
            if result:
                self.send_header('Location', point.success_url)
            else:
                self.send_header('Location', point.error_url)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd server on port {port}')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
