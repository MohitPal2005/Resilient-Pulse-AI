import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google.cloud import bigquery
import vertexai
from vertexai.generative_models import GenerativeModel

# Load environment variables (GCP credentials)
load_dotenv()

app = Flask(__name__)
# Enable CORS so your React frontend can talk to this API later
CORS(app)

# Initialize Google Cloud clients
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION")

# Initialize Vertex AI for Gemini
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    # Using Gemini 1.5 Flash for high-speed, cost-effective hackathon responses
    ai_model = GenerativeModel("gemini-2.5-flash") 
    bq_client = bigquery.Client(project=PROJECT_ID)
    print("✅ Successfully connected to Google Cloud & Vertex AI!")
except Exception as e:
    print(f"⚠️ Error initializing cloud clients: {e}")

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ResilientPulse AI Backend is running!"})

@app.route('/api/chat', methods=['POST'])
def chat_with_city_data():
    try:
        user_message = request.json.get('message', 'What is the current traffic risk?')
        
        # 1. RETRIEVE: Query BigQuery for the highest congestion risk zones
        # We pull the top 5 highest risk areas to give Gemini context.
        query = f"""
            SELECT PULocationID, pickup_hour, trip_distance, fare_amount, congestion_risk 
            FROM `{PROJECT_ID}.urban_intelligence.congestion_metrics`
            ORDER BY congestion_risk DESC 
            LIMIT 5
        """
        query_job = bq_client.query(query)
        results = query_job.result()
        
        # Format the data into a readable string for the AI
        live_data_context = "LIVE CITY CONGESTION DATA (Top 5 Risk Zones):\n"
        for row in results:
            live_data_context += f"- Location ID {row['PULocationID']} at Hour {row['pickup_hour']}: Risk Score {row['congestion_risk']:.2f}, Avg Speed/Dist: {row['trip_distance']:.2f} miles.\n"

        # 2. AUGMENT: Create the smart prompt
        prompt = f"""
        You are 'ResilientPulse', an advanced AI City Commander for urban planners and emergency responders.
        Use the following real-time data from our BigQuery database to answer the user's question accurately.
        
        {live_data_context}
        
        User Question: {user_message}
        
        Instructions:
        - Be concise, professional, and directly answer the question.
        - If the user asks about dangerous zones, refer to the Location IDs with the highest risk scores.
        - Suggest a quick actionable decision (e.g., "Reroute transit away from Location X").
        """

        # 3. GENERATE: Ask Gemini!
        response = ai_model.generate_content(prompt)
        
        return jsonify({
            "status": "success",
            "reply": response.text,
            "data_used": live_data_context
        })

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Run the Flask app on port 8080 (Cloud Run's default port)
    app.run(debug=True, host='0.0.0.0', port=8080)