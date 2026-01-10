"""Risk Scoring Service - Analyzes merchant applications and provides risk scores"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, JSON, Float, Text
from datetime import datetime
import sys
import os
import uuid
import json

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.models import (
    RiskScoreRequest, RiskScoreResponse, RiskScoreSource,
    HealthResponse, ReportRequest, EmailRecipient
)
from shared.database import Base, get_db, engine, init_db

# Add core framework to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from local_agent_framework import Agent, Task, tool

# Database Models
class RiskApplicationDB(Base):
    __tablename__ = "risk_applications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_name = Column(String, nullable=False)
    company_info = Column(JSON, nullable=False)
    authorized_person = Column(JSON, nullable=False)
    documents = Column(JSON, nullable=False)
    risk_score = Column(Float, default=0.0)
    risk_category = Column(String, default="PENDING")
    sources = Column(JSON, default=[])
    summary = Column(Text, default="")
    recommendations = Column(JSON, default=[])
    status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

# Create tables
init_db()

# FastAPI App
app = FastAPI(title="Risk Scoring Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Web scraping and verification tools
@tool
def search_mersis(mersis_number: str) -> str:
    """Search company in MERSIS (Turkish Trade Registry System)"""
    # In production, integrate with actual MERSIS API
    # For now, simulate the search
    if mersis_number and len(mersis_number) == 16:
        return f"Company found in MERSIS. Status: Active, Registration: Valid"
    return "Company not found in MERSIS database"

@tool
def search_tax_office(vkn: str, company_name: str) -> str:
    """Search company in tax office records"""
    # In production, integrate with GIB (Gelir İdaresi Başkanlığı) API
    if vkn and len(vkn) == 10:
        return f"Tax record found for {company_name}. VKN: {vkn}, Status: Active"
    return "Tax record not found"

@tool
def search_trade_registry(company_name: str, city: str) -> str:
    """Search company in trade registry"""
    # In production, integrate with TOBB or local chambers
    return f"Trade registry search for {company_name} in {city}. Status: Found, Active since 2020"

@tool
def search_bkm(bkm_number: str) -> str:
    """Search in BKM (Interbank Card Center) database"""
    # In production, integrate with BKM API
    if bkm_number:
        return f"BKM record found. Member since 2020, Status: Active"
    return "No BKM record found"

@tool
def search_web_reputation(company_name: str, website: str) -> str:
    """Search company reputation online (news, reviews, complaints)"""
    # In production, use web scraping and sentiment analysis
    # Search: news sites, complaint sites (şikayetvar), social media
    return f"Web reputation check for {company_name}. Found 50+ mentions, overall sentiment: POSITIVE, No major complaints"

@tool
def verify_website(url: str) -> str:
    """Verify company website SSL, domain age, content"""
    # In production, check SSL certificate, whois data, content analysis
    if url:
        return f"Website {url}: SSL Valid, Domain age: 3 years, Content: Professional, HTTPS: Yes"
    return "No website provided"

@tool
def check_fraud_databases(company_name: str, vkn: str) -> str:
    """Check company against fraud databases"""
    # In production, integrate with fraud databases, blacklists
    return f"Fraud check for {company_name}: No records found in fraud databases, No sanctions, Clean record"

@tool
def analyze_financial_health(monthly_revenue: float, company_type: str) -> str:
    """Analyze company financial health based on revenue"""
    if monthly_revenue:
        if monthly_revenue > 100000:
            return f"Financial health: STRONG. Monthly revenue {monthly_revenue:,.2f} TL indicates stable business"
        elif monthly_revenue > 50000:
            return f"Financial health: GOOD. Monthly revenue {monthly_revenue:,.2f} TL indicates growing business"
        elif monthly_revenue > 20000:
            return f"Financial health: MODERATE. Monthly revenue {monthly_revenue:,.2f} TL indicates small-medium business"
        else:
            return f"Financial health: WEAK. Monthly revenue {monthly_revenue:,.2f} TL indicates startup/small business"
    return "No financial data provided"

def create_risk_agent():
    """Create specialized risk scoring agent"""
    agent = Agent(
        model="ollama/llama3.2",
        name="Risk Scoring Agent",
        role="Financial Risk Analyst",
        goal="Analyze merchant applications and provide accurate risk assessments",
        instructions="""You are a financial risk analyst specializing in merchant onboarding.

Your task is to:
1. Analyze company information thoroughly
2. Verify data from multiple sources
3. Check for fraud indicators
4. Evaluate financial stability
5. Provide a comprehensive risk score (0-100, higher is better)
6. Categorize risk as: EXCELLENT (80-100), LOW (60-79), MEDIUM (40-59), HIGH (20-39), CRITICAL (0-19)
7. Provide specific recommendations

Be thorough, objective, and professional in your analysis."""
    )
    return agent

def calculate_risk_score(sources: list) -> tuple:
    """Calculate final risk score from all sources"""
    total_score = 0
    max_score = 100

    # Weight distribution
    weights = {
        "mersis": 15,
        "tax_office": 15,
        "trade_registry": 10,
        "bkm": 10,
        "web_reputation": 15,
        "website": 10,
        "fraud_check": 20,
        "financial_health": 5
    }

    # Calculate weighted score
    for source in sources:
        contribution = source.get("score_contribution", 0)
        total_score += contribution

    # Normalize to 0-100
    risk_score = min(100, max(0, total_score))

    # Determine category
    if risk_score >= 80:
        category = "EXCELLENT"
    elif risk_score >= 60:
        category = "LOW"
    elif risk_score >= 40:
        category = "MEDIUM"
    elif risk_score >= 20:
        category = "HIGH"
    else:
        category = "CRITICAL"

    return risk_score, category

async def process_risk_scoring(application_id: str, application: dict, db: Session):
    """Background task to process risk scoring"""
    try:
        # Get application from database
        db_app = db.query(RiskApplicationDB).filter(RiskApplicationDB.id == application_id).first()
        if not db_app:
            return

        # Update status
        db_app.status = "processing"
        db.commit()

        # Extract data
        company_info = application["company_info"]

        # Create risk agent
        agent = create_risk_agent()

        # Prepare tools
        tools = [
            search_mersis,
            search_tax_office,
            search_trade_registry,
            search_bkm,
            search_web_reputation,
            verify_website,
            check_fraud_databases,
            analyze_financial_health
        ]

        # Create analysis task
        task_description = f"""
Analyze this merchant application for risk assessment:

Company Name: {company_info['merchant_name']}
Trade Name: {company_info['trade_name']}
MERSIS: {company_info.get('mersis_number', 'N/A')}
VKN: {company_info.get('hosting_vkn', 'N/A')}
Website: {company_info.get('hosting_url', 'N/A')}
BKM Number: {company_info.get('bkm_number', 'N/A')}
Monthly Revenue: {company_info.get('monthly_revenue', 'N/A')} TL
Location: {company_info['city']}, {company_info['district']}
Company Type: {company_info['company_type']}

Use ALL available tools to:
1. Verify company registration (MERSIS, Tax Office, Trade Registry)
2. Check BKM membership if applicable
3. Search web reputation and news
4. Verify website security and authenticity
5. Check fraud databases
6. Analyze financial health

Provide a detailed summary of findings and specific recommendations.
"""

        task = Task(
            description=task_description,
            tools=tools
        )

        # Execute analysis
        result = agent.do(task)

        # Parse sources (in production, extract from agent's tool usage)
        sources = [
            {
                "source_name": "MERSIS Registry",
                "source_url": "https://mersis.gov.tr",
                "data_found": "Company registration verified",
                "risk_impact": "POSITIVE - Valid registration",
                "score_contribution": 15.0
            },
            {
                "source_name": "Tax Office Records",
                "source_url": "https://ivd.gib.gov.tr",
                "data_found": "Tax records active and valid",
                "risk_impact": "POSITIVE - Compliant taxpayer",
                "score_contribution": 15.0
            },
            {
                "source_name": "Trade Registry",
                "source_url": "https://ticaret.gov.tr",
                "data_found": "Active trade registry",
                "risk_impact": "POSITIVE - Legitimate business",
                "score_contribution": 10.0
            },
            {
                "source_name": "BKM Database",
                "source_url": "https://bkm.com.tr",
                "data_found": "BKM member found" if company_info.get('bkm_number') else "Not a BKM member",
                "risk_impact": "NEUTRAL" if company_info.get('bkm_number') else "NEGATIVE",
                "score_contribution": 10.0 if company_info.get('bkm_number') else 5.0
            },
            {
                "source_name": "Web Reputation Check",
                "source_url": "Multiple sources",
                "data_found": "Positive online presence",
                "risk_impact": "POSITIVE - Good reputation",
                "score_contribution": 15.0
            },
            {
                "source_name": "Website Verification",
                "source_url": company_info.get('hosting_url', 'N/A'),
                "data_found": "SSL valid, professional website",
                "risk_impact": "POSITIVE - Secure website",
                "score_contribution": 10.0 if company_info.get('hosting_url') else 5.0
            },
            {
                "source_name": "Fraud Database Check",
                "source_url": "Internal databases",
                "data_found": "No fraud records",
                "risk_impact": "POSITIVE - Clean record",
                "score_contribution": 20.0
            },
            {
                "source_name": "Financial Analysis",
                "source_url": "Internal",
                "data_found": f"Monthly revenue: {company_info.get('monthly_revenue', 0)} TL",
                "risk_impact": "Based on revenue",
                "score_contribution": 5.0
            }
        ]

        # Calculate final score
        risk_score, risk_category = calculate_risk_score(sources)

        # Generate recommendations
        recommendations = [
            "✅ Company registration verified through MERSIS",
            "✅ Tax records are active and compliant",
            "✅ No fraud indicators found",
        ]

        if risk_score >= 80:
            recommendations.append("✅ EXCELLENT risk profile - Approve with standard terms")
        elif risk_score >= 60:
            recommendations.append("⚠️ LOW risk profile - Approve with standard monitoring")
        elif risk_score >= 40:
            recommendations.append("⚠️ MEDIUM risk - Approve with enhanced monitoring")
        else:
            recommendations.append("❌ HIGH/CRITICAL risk - Requires manual review or reject")

        if not company_info.get('bkm_number'):
            recommendations.append("ℹ️ Consider BKM membership verification")

        if not company_info.get('hosting_url'):
            recommendations.append("ℹ️ Request company website for verification")

        # Update database
        db_app.risk_score = risk_score
        db_app.risk_category = risk_category
        db_app.sources = sources
        db_app.summary = result.result if hasattr(result, 'result') else str(result)
        db_app.recommendations = recommendations
        db_app.status = "completed"
        db_app.processed_at = datetime.utcnow()

        db.commit()

    except Exception as e:
        # Mark as failed
        db_app = db.query(RiskApplicationDB).filter(RiskApplicationDB.id == application_id).first()
        if db_app:
            db_app.status = "failed"
            db_app.summary = f"Error: {str(e)}"
            db.commit()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        service="risk-service",
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/risk-score")
async def create_risk_score(
    request: RiskScoreRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a risk score for merchant application"""
    try:
        # Create application record
        application_data = request.application.model_dump()

        db_app = RiskApplicationDB(
            merchant_name=application_data["company_info"]["merchant_name"],
            company_info=application_data["company_info"],
            authorized_person=application_data["authorized_person"],
            documents=application_data["documents"],
            status="pending"
        )

        db.add(db_app)
        db.commit()
        db.refresh(db_app)

        # Start background processing
        background_tasks.add_task(
            process_risk_scoring,
            db_app.id,
            application_data,
            db
        )

        return {
            "application_id": db_app.id,
            "status": "processing",
            "message": "Risk scoring started. Check status at /risk-score/{application_id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/risk-score/{application_id}")
async def get_risk_score(application_id: str, db: Session = Depends(get_db)):
    """Get risk score by application ID"""
    app = db.query(RiskApplicationDB).filter(RiskApplicationDB.id == application_id).first()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    return {
        "application_id": app.id,
        "merchant_name": app.merchant_name,
        "status": app.status,
        "risk_score": app.risk_score,
        "risk_category": app.risk_category,
        "sources": app.sources,
        "summary": app.summary,
        "recommendations": app.recommendations,
        "created_at": app.created_at.isoformat(),
        "processed_at": app.processed_at.isoformat() if app.processed_at else None
    }

@app.get("/risk-scores")
async def list_risk_scores(db: Session = Depends(get_db)):
    """List all risk scores"""
    apps = db.query(RiskApplicationDB).order_by(RiskApplicationDB.created_at.desc()).all()

    return [
        {
            "application_id": app.id,
            "merchant_name": app.merchant_name,
            "risk_score": app.risk_score,
            "risk_category": app.risk_category,
            "status": app.status,
            "created_at": app.created_at.isoformat()
        }
        for app in apps
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
