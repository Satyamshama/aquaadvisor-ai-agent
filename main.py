from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI(title="AquaAdvisor AI Agent", description="Water Quality Expert AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq API setup (FREE with signup at console.groq.com)
GROQ_API_KEY = "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"  # Replace with your Groq API Key if regenerated
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str

def get_groq_response(message):
    """Get response from Groq free API"""
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {
                    "role": "system",
                    "content": "You are AquaAdvisor, a water quality expert. Provide practical advice about pH levels (6.5-8.5 ideal), TDS values, and water purification methods. Keep responses under 100 words."
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            print("Groq API fallback – Status:", response.status_code)
            return get_mock_response(message)
    except Exception as e:
        print(f"Groq API Error: {e}")
        return get_mock_response(message)

#def get_mock_response(message):
    """Domain-specific fallback responses"""
    message_lower = message.lower()
    if "ph" in message_lower:
        if any(val in message_lower for val in ["9", "10", "11", "alkaline", "high ph"]):
            return "pH above 8.5 is alkaline and may cause scale buildup, bitter taste, and pipe damage. Consider a pH adjustment filter."
        elif any(val in message_lower for val in ["5", "4", "acidic", "low ph"]):
            return "pH below 6.5 is acidic and may corrode pipes and cause a metallic taste. You may need alkaline treatment or professional testing."
        else:
            return "Safe pH for drinking water is 6.5 to 8.5. Use strips or a digital pH meter to test your water."
    elif "tds" in message_lower or "ppm" in message_lower or "dissolved" in message_lower:
        if any(val in message_lower for val in ["600", "700", "800", "900", "1000"]):
            return "TDS above 500 ppm often means excess minerals; use RO purification for safer drinking water."
        elif any(val in message_lower for val in ["50", "100", "low tds"]):
            return "TDS below 150 ppm may lack essential minerals like calcium and magnesium. Consider mineral supplementation."
        else:
            return "TDS values between 150-300 ppm are good for drinking water. Test with a TDS meter regularly."
    elif any(word in message_lower for word in ["filter", "purify", "boil", "ro", "uv", "clean"]):
        return "Boiling kills microbes; RO removes TDS; UV eliminates pathogens; carbon filters remove chlorine and odor. Choose based on your issue."
    elif any(word in message_lower for word in ["chlorine", "taste", "smell", "metallic", "bitter"]):
        return "Chlorine or metallic taste can be removed using activated carbon filters. Bitter taste is common with high pH water."
    elif any(word in message_lower for word in ["safe", "test", "professional", "dangerous"]):
        return "Get professional water testing if you notice unusual taste or smell, have ongoing health issues, or use a private well."
    else:
        return "I'm AquaAdvisor! Ask me about pH, TDS (minerals), filtration, purification, or how to keep your drinking water safe."

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(chat_message: ChatMessage):
    ai_response = get_groq_response(chat_message.message)
    return ChatResponse(response=ai_response, session_id=chat_message.session_id)

@app.get("/")
async def root():
    return {
        "message": "AquaAdvisor AI Agent is running!",
        "version": "1.0",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    from datetime import datetime
    return {"status": "healthy", "agent": "AquaAdvisor", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
