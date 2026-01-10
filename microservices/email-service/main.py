"""Email Service - Sends risk score reports to departments"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.models import HealthResponse, ReportRequest, EmailRecipient
from shared.database import get_db

# FastAPI App
app = FastAPI(title="Email Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_risk_report_html(risk_data: dict) -> str:
    """Generate HTML email report"""
    risk_score = risk_data.get("risk_score", 0)
    risk_category = risk_data.get("risk_category", "UNKNOWN")
    merchant_name = risk_data.get("merchant_name", "N/A")
    sources = risk_data.get("sources", [])
    recommendations = risk_data.get("recommendations", [])
    summary = risk_data.get("summary", "No summary available")

    # Color based on risk category
    color_map = {
        "EXCELLENT": "#10b981",
        "LOW": "#3b82f6",
        "MEDIUM": "#f59e0b",
        "HIGH": "#ef4444",
        "CRITICAL": "#dc2626"
    }
    color = color_map.get(risk_category, "#6b7280")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px 10px 0 0;
                text-align: center;
            }}
            .score-card {{
                background: {color};
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px;
                margin: 20px 0;
            }}
            .score {{
                font-size: 48px;
                font-weight: bold;
            }}
            .category {{
                font-size: 24px;
                margin-top: 10px;
            }}
            .section {{
                background: #f9fafb;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                border-left: 4px solid {color};
            }}
            .section h2 {{
                color: #1f2937;
                margin-top: 0;
            }}
            .source {{
                background: white;
                padding: 15px;
                margin: 10px 0;
                border-radius: 6px;
                border-left: 3px solid #3b82f6;
            }}
            .source-name {{
                font-weight: bold;
                color: #1f2937;
            }}
            .recommendation {{
                background: white;
                padding: 12px;
                margin: 8px 0;
                border-radius: 6px;
                display: flex;
                align-items: center;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                color: #6b7280;
                border-top: 1px solid #e5e7eb;
                margin-top: 30px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #e5e7eb;
            }}
            th {{
                background: #f3f4f6;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Risk Skorlama Raporu</h1>
            <p>Merchant Onboarding Risk Analizi</p>
        </div>

        <div class="score-card">
            <div class="score">{risk_score:.1f}/100</div>
            <div class="category">Risk Kategorisi: {risk_category}</div>
            <p style="margin-top: 10px;">{merchant_name}</p>
        </div>

        <div class="section">
            <h2>📊 Analiz Özeti</h2>
            <p>{summary}</p>
        </div>

        <div class="section">
            <h2>🔍 Veri Kaynakları ve Skorlama</h2>
            {''.join(f'''
            <div class="source">
                <div class="source-name">{source.get('source_name', 'N/A')}</div>
                <table>
                    <tr>
                        <th>Kaynak URL</th>
                        <td>{source.get('source_url', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>Bulunan Veri</th>
                        <td>{source.get('data_found', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>Risk Etkisi</th>
                        <td>{source.get('risk_impact', 'N/A')}</td>
                    </tr>
                    <tr>
                        <th>Skor Katkısı</th>
                        <td><strong>{source.get('score_contribution', 0):.1f} puan</strong></td>
                    </tr>
                </table>
            </div>
            ''' for source in sources)}
        </div>

        <div class="section">
            <h2>💡 Öneriler</h2>
            {''.join(f'<div class="recommendation">{rec}</div>' for rec in recommendations)}
        </div>

        <div class="section">
            <h2>📋 Rapor Bilgileri</h2>
            <table>
                <tr>
                    <th>Rapor Tarihi</th>
                    <td>{datetime.utcnow().strftime('%d.%m.%Y %H:%M')}</td>
                </tr>
                <tr>
                    <th>Analiz Sistemi</th>
                    <td>Local Agent Framework - Risk Scoring Service</td>
                </tr>
                <tr>
                    <th>Analiz Aracı</th>
                    <td>AI-Powered Risk Agent (Ollama/llama3.2)</td>
                </tr>
            </table>
        </div>

        <div class="footer">
            <p><strong>Bu rapor otomatik olarak oluşturulmuştur.</strong></p>
            <p>Risk & Compliance Department | Merchant Onboarding System</p>
            <p style="font-size: 12px; margin-top: 10px;">
                Bu e-posta gizli bilgiler içermektedir. Yetkili alıcı değilseniz lütfen silerek bildirin.
            </p>
        </div>
    </body>
    </html>
    """
    return html

def send_email_smtp(recipient_email: str, subject: str, html_content: str):
    """Send email via SMTP (for production, configure real SMTP server)"""
    # For demo purposes, we'll just log the email
    # In production, configure SMTP settings
    """
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = recipient_email

    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
    """

    # For demo: just log
    print(f"\n{'='*60}")
    print(f"📧 EMAIL SENT TO: {recipient_email}")
    print(f"📨 SUBJECT: {subject}")
    print(f"{'='*60}\n")
    return True

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        service="email-service",
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/send-report")
async def send_risk_report(request: ReportRequest):
    """Send risk score report to specified recipients"""
    try:
        # In production, fetch risk score data from risk-service
        # For now, we'll create a mock response
        import httpx

        # Fetch risk score from risk-service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"http://localhost:8004/risk-score/{request.risk_score_id}"
            )

            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Risk score not found")

            risk_data = response.json()

        # Generate HTML report
        html_content = generate_risk_report_html(risk_data)

        # Send to all recipients
        sent_count = 0
        for recipient in request.recipients:
            subject = f"Risk Skorlama Raporu - {risk_data.get('merchant_name', 'N/A')} [{risk_data.get('risk_category', 'N/A')}]"

            # Send email
            send_email_smtp(recipient.email, subject, html_content)
            sent_count += 1

        return {
            "status": "success",
            "message": f"Report sent to {sent_count} recipients",
            "recipients": [{"department": r.department, "email": r.email} for r in request.recipients]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-test-email")
async def send_test_email(email: str):
    """Send test email"""
    try:
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #667eea;">✅ Email Service Test</h2>
            <p>This is a test email from the Email Service.</p>
            <p>If you received this, the email service is working correctly!</p>
        </body>
        </html>
        """

        send_email_smtp(email, "Test Email - Email Service", html_content)

        return {
            "status": "success",
            "message": f"Test email sent to {email}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
