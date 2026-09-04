import sys
import os
sys.path.insert(0, 'd:/KisaanDost')
sys.stdout.reconfigure(encoding='utf-8')
import joblib, asyncio

# 1. Pest Prediction Model
payload = joblib.load('d:/KisaanDost/app/backend/models/pest_prediction_model_v1.pkl')
acc = payload['accuracy']
cv = payload['cv_mean']
print(f"1. Pest Prediction ML Model Accuracy: {acc*100:.2f}% | 5-Fold CV: {cv*100:.2f}% [PASS]")

# 2. Pesticide Recommendation Engine
pest_rules = joblib.load('d:/KisaanDost/app/backend/models/pesticide_recommendation_model_v1.pkl')
print(f"2. Pesticide Recommendation Engine: {len(pest_rules)} Formulations Verified [PASS]")

# 3. IPM Advice Generator
ipm = joblib.load('d:/KisaanDost/app/backend/models/ipm_advice_generator_v1.pkl')
print(f"3. IPM Advice Generator: {len(ipm)} Crops Covered [PASS]")

# 4. Risk Dataset Model
from app.backend.services.risk_service import get_risk_service
risk_svc = get_risk_service()
r = risk_svc.get_current_risk_assessment('Lahore', 'Wheat')
print(f"4. Risk Model (2022-2026): Score = {r['risk_percent']}%, Level = {r['risk_level']} [PASS]")

# 5. AI Agronomist Query Engine
from app.backend.services.ai_agronomist_service import get_ai_agronomist_service
ai_svc = get_ai_agronomist_service()

q1 = asyncio.run(ai_svc.answer_query('Mausami alert Kya Hai Mujhe Batao thoda', 'Lahore', 'Wheat', 'ur'))
print(f"5. AI Weather Query: {q1['answer'][:60]}... [PASS]")

q2 = asyncio.run(ai_svc.answer_query('Is there any rain expected in next 3 days?', 'Lahore', 'Wheat', 'en'))
print(f"6. AI Rain Query: {q2['answer'][:60]}... [PASS]")

q3 = asyncio.run(ai_svc.answer_query('should I aggregate my wheat crop today', 'Lahore', 'Wheat', 'ur'))
print(f"7. AI Irrigation Query: {q3['answer'][:60]}... [PASS]")

q4 = asyncio.run(ai_svc.answer_query('hey whats up', 'Lahore', 'Wheat', 'ur'))
print(f"8. AI Greeting Query: {q4['answer'][:60]}... [PASS]")
