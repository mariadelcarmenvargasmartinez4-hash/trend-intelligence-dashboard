from flask import Flask, render_template, request
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI

# ==============================
# CONFIGURACIÓN INICIAL
# ==============================
load_dotenv()

app = Flask(__name__)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


# ==============================
# FUNCIÓN YOUTUBE
# ==============================
def get_youtube_videos(keyword):
    if not YOUTUBE_API_KEY:
        print("ERROR: YOUTUBE_API_KEY no está configurada")
        return []

    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "maxResults": 5,
        "key": YOUTUBE_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        videos = []
        for item in data.get("items", []):
            videos.append({
                "title": item["snippet"]["title"],
                "description": item["snippet"]["description"],
                "url": f'https://www.youtube.com/watch?v={item["id"]["videoId"]}',
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                "channel": item["snippet"]["channelTitle"]
            })

        return videos

    except requests.exceptions.RequestException as e:
        print("Error YouTube:", e)
        return []


# ==============================
# FUNCIÓN TENDENCIA
# ==============================
def calculate_trend(news_count, video_count):
    score = (news_count * 2) + (video_count * 1)

    if score >= 12:
        level = "Alta 🔥"
    elif score >= 6:
        level = "Media ⚡"
    else:
        level = "Baja ❄️"

    return level, score

# ==============================
# FUNCIÓN IA ESPECIALISTA
# ==============================
def get_ai_analysis(keyword):
    if not OPENAI_API_KEY:
        return "No se configuró la API de OpenAI."

    prompt = f"""
    Actúa como un especialista en tecnología.
    Explica qué es {keyword}.
    Explica por qué es relevante actualmente.
    Indica si está en tendencia y por qué.
    Responde en máximo 8 líneas claras y profesionales.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        print("Error OpenAI:", e)
        return "No se pudo generar el análisis IA."


# ==============================
# RUTA PRINCIPAL
# ==============================
@app.route("/", methods=["GET", "POST"])
def home():
    articles = []
    videos = []
    trend = None
    ai_analysis = None

    if request.method == "POST":
        keyword = request.form.get("keyword")

        if not keyword or keyword.strip() == "":
            return render_template(
                "index.html",
                articles=[],
                videos=[],
                trend="Ingresa una palabra clave",
                ai_analysis=None
            )

        # ==========================
        # NOTICIAS
        # ==========================
        if NEWS_API_KEY:
            news_url = "https://newsapi.org/v2/everything"
            news_params = {
                "q": keyword,
                "apiKey": NEWS_API_KEY,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 5
            }

            try:
                news_response = requests.get(news_url, params=news_params, timeout=5)
                news_response.raise_for_status()
                news_data = news_response.json()

                if news_data.get("status") == "ok":
                    articles = news_data.get("articles", [])
                else:
                    print("NewsAPI error:", news_data.get("message"))

            except requests.exceptions.RequestException as e:
                print("Error NewsAPI:", e)
        else:
            print("ERROR: NEWS_API_KEY no está configurada")

        # ==========================
        # VIDEOS YOUTUBE
        # ==========================
        videos = get_youtube_videos(keyword)

        # ==========================
        # CALCULAR TENDENCIA
        # ==========================
        trend, trend_score = calculate_trend(len(articles), len(videos))

        # ==========================
        # IA ESPECIALISTA
        # ==========================
        ai_analysis = get_ai_analysis(keyword)

    return render_template(
    "index.html",
    articles=articles,
    videos=videos,
    trend=trend,
    trend_score=trend_score,
    ai_analysis=ai_analysis
)

# ==============================
# EJECUCIÓN
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
