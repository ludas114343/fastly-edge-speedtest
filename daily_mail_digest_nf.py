import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.request
import urllib.parse
import json
import time
import os
import sys
import re
from datetime import datetime, timedelta

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Configuration & Env
GMAIL_USER = os.environ.get("GMAIL_USER", "luotianyi983@gmail.com")
GMAIL_APP_PW = os.environ.get("GMAIL_APP_PW", "xpvivybiftuxhtxr").replace(" ", "")
OUTLOOK_USER = os.environ.get("OUTLOOK_USER", "luotianyi1919@outlook.com")
AGNES_BASE = os.environ.get("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1")
AGNES_KEY = os.environ.get("AGNES_API_KEY", "wk-16wJgCQvuAnyAUxIxfiXwSGbr43kopg7ScOoiztK9wPDFHY1")
AGNES_MODEL = os.environ.get("AGNES_MODEL", "agnes-2.5-flash")
DRV_BASE = os.environ.get("DRV_BASE", "https://drv.ruoyemu.asia")
ACCESS_PW = os.environ.get("ACCESS_PASSWORD", "710223")

# Load fallbacks if running locally
if not GMAIL_APP_PW or not AGNES_KEY:
    for env_path in [r"D:\tools\ai-hub\.env.production.local", r"C:\Users\ludas\.env"]:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k == "GMAIL_APP_PW" and not GMAIL_APP_PW:
                            GMAIL_APP_PW = v.replace(" ", "")
                        elif k == "AGNES_API_KEY" and not AGNES_KEY:
                            AGNES_KEY = v
                        elif k == "AGNES_BASE_URL" and AGNES_BASE == "https://apihub.agnes-ai.com/v1":
                            AGNES_BASE = v
                        elif k == "AGNES_MODEL" and AGNES_MODEL == "agnes-2.5-flash":
                            AGNES_MODEL = v
                        elif k == "ACCESS_PASSWORD" and ACCESS_PW == "710223":
                            ACCESS_PW = v

USER_MEMORY = (
    "用户是鲁天佑（Lu Tianyou），上海高中生，正在准备2027 Fall美国大学本科申请，主攻电气工程(EE/ECE)与计算机(CS)，"
    "家庭年收入低于1万美元，极度需要NEED-BASED全额/半额助学金。重点关注大学申请截止日期、CSS Profile/ISFAA助学金豁免与审核进展、"
    "面试邀请、招生宣讲会、Portal状态更新等重要邮件。"
)

def decode_mime(header_val):
    if not header_val:
        return ""
    fragments = decode_header(header_val)
    res = []
    for text, enc in fragments:
        if isinstance(text, bytes):
            res.append(text.decode(enc or "utf-8", errors="ignore"))
        else:
            res.append(str(text))
    return "".join(res)

def strip_tags(html):
    html = re.sub(r"<style[\s\S]*?</style>", "", html, flags=re.I)
    html = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"&nbsp;", " ", html)
    html = re.sub(r"&amp;", "&", html)
    html = re.sub(r"&lt;", "<", html)
    html = re.sub(r"&gt;", ">", html)
    html = re.sub(r"&quot;", '"', html)
    html = re.sub(r"\s+", " ", html)
    return html.strip()

def extract_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdisp = str(part.get("Content-Disposition"))
            if ctype == "text/plain" and "attachment" not in cdisp:
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
                    break
        if not body:
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = strip_tags(payload.decode(part.get_content_charset() or "utf-8", errors="ignore"))
                        break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            raw = payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")
            body = strip_tags(raw) if msg.get_content_type() == "text/html" else raw
    return body[:600].strip()

def get_outlook_access_token():
    """Fetch token from Cloudflare R2, refresh if within 5 min of expiry, save back to R2."""
    print("[1/5] Fetching Outlook OAuth2 Token from R2...")
    req = urllib.request.Request(
        f"{DRV_BASE}/download?b=lty&p=outlook-token.json",
        headers={"x-auth": ACCESS_PW, "User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=12) as r:
        token_data = json.loads(r.read().decode("utf-8"))

    refresh_token = token_data.get("refresh_token")
    expires_at = token_data.get("expires_at", 0)

    # Valid if > 5 mins remaining
    if token_data.get("access_token") and expires_at and time.time() < (expires_at / 1000.0 - 300):
        print("  -> Using valid cached access_token from R2")
        return token_data["access_token"]

    print("  -> Token near expiry, refreshing via Microsoft OAuth2 endpoint...")
    post_data = urllib.parse.urlencode({
        "client_id": "9e5f94bc-e8a4-4e73-b8be-63364c29d753",
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "offline_access https://outlook.office.com/IMAP.AccessAsUser.All https://outlook.office.com/SMTP.Send"
    }).encode("utf-8")

    r_req = urllib.request.Request(
        "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        data=post_data,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(r_req, timeout=15) as r:
        j = json.loads(r.read().decode("utf-8"))
        access_token = j["access_token"]
        new_refresh = j.get("refresh_token", refresh_token)
        expires_in = j.get("expires_in", 3600)
        token_data["access_token"] = access_token
        token_data["refresh_token"] = new_refresh
        token_data["expires_at"] = int(time.time() + expires_in) * 1000

    # Save back to R2
    upload_req = urllib.request.Request(
        f"{DRV_BASE}/upload?b=lty&p=outlook-token.json",
        data=json.dumps(token_data).encode("utf-8"),
        headers={"x-auth": ACCESS_PW, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(upload_req, timeout=12) as _:
        pass
    print("  -> Successfully refreshed and saved token back to R2!")
    return access_token

def fetch_gmail_emails(days=2, limit=25):
    print(f"[2/5] Fetching Gmail emails (last {days} days)...")
    if not GMAIL_USER or not GMAIL_APP_PW:
        print("  -> Warning: GMAIL_USER or GMAIL_APP_PW missing, skipping Gmail")
        return []

    items = []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(GMAIL_USER, GMAIL_APP_PW)
        mail.select("INBOX", readonly=True)

        since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
        status, data = mail.search(None, f'(SINCE "{since_date}")')
        if status != "OK" or not data[0]:
            status, data = mail.search(None, "ALL")

        msg_ids = data[0].split()
        recent_ids = msg_ids[-limit:] if msg_ids else []
        for mid in recent_ids:
            try:
                _, msg_data = mail.fetch(mid, "(RFC822)")
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)
                subj = decode_mime(msg.get("Subject", "(no subject)"))
                from_ = decode_mime(msg.get("From", "unknown"))
                date_ = msg.get("Date", "")
                body_ = extract_body(msg)
                items.append({
                    "acc": "Gmail",
                    "from": from_,
                    "subject": subj,
                    "date": date_,
                    "text": body_
                })
            except Exception as e:
                pass
        mail.close()
        mail.logout()
        print(f"  -> Successfully fetched {len(items)} emails from Gmail")
    except Exception as e:
        print(f"  -> Gmail fetch error: {e}")
    return items

def fetch_outlook_emails(days=2, limit=25):
    print(f"[3/5] Fetching Outlook emails (last {days} days)...")
    items = []
    try:
        access_token = get_outlook_access_token()
        mail = imaplib.IMAP4_SSL("outlook.office365.com", 993)
        auth_string = f"user={OUTLOOK_USER}\x01auth=Bearer {access_token}\x01\x01"
        mail.authenticate("XOAUTH2", lambda x: auth_string)
        mail.select("INBOX", readonly=True)

        since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
        status, data = mail.search(None, f'(SINCE "{since_date}")')
        if status != "OK" or not data[0]:
            status, data = mail.search(None, "ALL")

        msg_ids = data[0].split()
        recent_ids = msg_ids[-limit:] if msg_ids else []
        for mid in recent_ids:
            try:
                _, msg_data = mail.fetch(mid, "(RFC822)")
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)
                subj = decode_mime(msg.get("Subject", "(no subject)"))
                from_ = decode_mime(msg.get("From", "unknown"))
                date_ = msg.get("Date", "")
                body_ = extract_body(msg)
                items.append({
                    "acc": "Outlook",
                    "from": from_,
                    "subject": subj,
                    "date": date_,
                    "text": body_
                })
            except Exception as e:
                pass
        mail.close()
        mail.logout()
        print(f"  -> Successfully fetched {len(items)} emails from Outlook")
    except Exception as e:
        print(f"  -> Outlook fetch error: {e}")
    return items

def generate_ai_summary(emails):
    print(f"[4/5] Generating AI Summary with Agnes AI ({AGNES_MODEL})...")
    if not emails:
        return "今日暂无新邮件。"

    # Build prompt
    lines = []
    for i, m in enumerate(emails[:35]):
        lines.append(f"[{i+1}] ({m['acc']}) {m['from']} | {m['subject']}\n    {m['text'][:250]}")
    emails_text = "\n".join(lines)

    prompt = (
        f"You are the user's daily email digest assistant. Summarize the emails below into a clean, concise Chinese digest.\n\n"
        f"--- USER PROFILE & PRIORITIES ---\n{USER_MEMORY}\n--- END PROFILE ---\n\n"
        f"--- FORMAT REQUIREMENTS ---\n"
        f"1. **🚨 紧急待办与核心事项**：需重点关注或行动的邮件（申请截止日期、补件通知、面试邀请、CSS/ISFAA助学金更新等，每条附带一行原因与截止日）；若无特别紧急写“今日暂无紧急待办”。\n"
        f"2. **ℹ️ 高校招生与申请动态**：大学推介、招生动态、宣讲会通知等常规动态简要分类梳理。\n"
        f"3. **💡 一句话总结**：今日邮件的核心总体概括。\n\n"
        f"--- EMAILS ({len(emails)} 封) ---\n{emails_text}"
    )

    req = urllib.request.Request(
        f"{AGNES_BASE}/chat/completions",
        data=json.dumps({
            "model": AGNES_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }).encode("utf-8"),
        headers={"Authorization": f"Bearer {AGNES_KEY}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        summary = data["choices"][0]["message"]["content"].strip()
        print("  -> AI Summary generated successfully!")
        return summary

def send_digest_email(summary, total_count):
    print(f"[5/5] Sending Digest Email to {OUTLOOK_USER} via Gmail SMTP...")
    date_str = datetime.now().strftime("%Y年%m月%d日")
    subject = f"📬 每日邮件总结 {date_str}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.7; color: #1f2937; background-color: #f9fafb; padding: 20px;">
      <div style="max-width: 650px; margin: 0 auto; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        <div style="border-bottom: 2px solid #2563eb; padding-bottom: 12px; margin-bottom: 20px;">
          <h2 style="margin: 0; color: #1e3a8a; font-size: 20px;">📬 每日申请邮箱早报 · {date_str}</h2>
          <p style="margin: 4px 0 0; color: #6b7280; font-size: 13px;">由 Northflank 云端原生任务自动生成（已扫描 {total_count} 封邮件）</p>
        </div>
        <div style="white-space: pre-wrap; font-size: 14px; color: #374151;">
{summary.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(chr(10), "<br>")}
        </div>
        <div style="margin-top: 28px; padding-top: 14px; border-top: 1px solid #f3f4f6; color: #9ca3af; font-size: 12px; text-align: center;">
          ⚡ Northflank Europe-West 原生容器定时投递 · 0 占用本地资源
        </div>
      </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["From"] = f"AI Mail Secretary <{GMAIL_USER}>"
    msg["To"] = OUTLOOK_USER
    msg["Subject"] = subject
    msg.attach(MIMEText(summary, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15)
    server.login(GMAIL_USER, GMAIL_APP_PW)
    server.sendmail(GMAIL_USER, [OUTLOOK_USER], msg.as_string())
    server.quit()
    print(f"  -> Digest email successfully sent to {OUTLOOK_USER}!")

def main():
    print(f"=== Starting Daily Mail Digest Job ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    gmail_emails = fetch_gmail_emails(days=2, limit=20)
    outlook_emails = fetch_outlook_emails(days=2, limit=20)

    # Filter out digests sent by ourselves to avoid recursion loops
    all_emails = [
        m for m in (gmail_emails + outlook_emails)
        if "每日邮件总结" not in m["subject"] and "Daily Email Summary" not in m["subject"]
    ]
    print(f"Total candidate emails to summarize: {len(all_emails)}")

    summary = generate_ai_summary(all_emails)
    print("\n--- Preview of AI Digest ---")
    print(summary[:300] + ("..." if len(summary) > 300 else ""))
    print("----------------------------\n")

    send_digest_email(summary, len(all_emails))
    print("=== Job Completed Successfully! ===")

if __name__ == "__main__":
    main()
