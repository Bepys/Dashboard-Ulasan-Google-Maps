import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Setup Streamlit
st.set_page_config(page_title="📍 Google Maps Review Dashboard", layout="wide", initial_sidebar_state="expanded")
st.markdown("<h1 style='color:#4FC3F7'>📍 Dashboard Ulasan Google Maps</h1>", unsafe_allow_html=True)

# Upload File
uploaded_file = st.sidebar.file_uploader("📎 Upload file CSV ulasan", type="csv")

# Stopwords
stopwords = {
    'yang', 'dan', 'untuk', 'dengan', 'juga', 'saya', 'kami', 'ada', 'itu', 'di', 'ke', 'dari', 'pada',
    'atau', 'tidak', 'karena', 'dalam', 'lagi', 'sudah', 'kalau', 'jadi', 'semua', 'bisa', 'aja', 'akan',
    'oleh', 'seperti', 'mau', 'nih', 'nya', 'cuma', 'hanya', 'the', 'and', 'but', 'was', 'with', 'you',
    'are', 'not', 'very', 'good', 'tempat', 'sangat', 'sekali', 'enak', 'banget', 'bintang', 'mantap',
    'baik', 'banyak', 'buat', 'cukup', 'disini', 'tapi', 'pasti', 'saat', 'dapat', 'memang', 'pun',
    'selama', 'serta', 'hingga', 'bahwa', 'tanpa', 'tentang'
}

# Fungsi Ekstraksi Kata
def most_common_words(text_series, top_n=20):
    words = []
    for text in text_series.dropna():
        tokens = re.findall(r'\b\w{3,}\b', text.lower())
        filtered = [word for word in tokens if word not in stopwords]
        words.extend(filtered)
    counter = Counter(words)
    return pd.DataFrame(counter.most_common(top_n), columns=["Kata", "Frekuensi"])

# Visualisasi Rating
def create_rating_plot(df):
    rating_counts = df['Star Given'].value_counts().sort_index().reset_index()
    rating_counts.columns = ['Rating', 'Jumlah']
    color_map = {1: '#EF5350', 2: '#FFCA28', 3: '#FFEE58', 4: '#66BB6A', 5: '#43A047'}
    fig = px.bar(rating_counts, x="Rating", y="Jumlah", title="Distribusi Rating",
                 color='Rating', color_discrete_map=color_map, text='Jumlah',
                 labels={'Rating': 'Bintang', 'Jumlah': 'Jumlah Ulasan'})
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(xaxis_title="Bintang", yaxis_title="Jumlah Ulasan")
    return fig

# Tren Bulanan
def create_monthly_trend(df):
    df["Month"] = df["Publish Date"].dt.to_period("M").astype(str)
    trend = df.groupby("Month").size().reset_index(name="Jumlah Review")
    fig = px.line(trend, x="Month", y="Jumlah Review", markers=True,
                  title="Tren Jumlah Review per Bulan", labels={'Month': 'Bulan', 'Jumlah Review': 'Jumlah Ulasan'})
    fig.update_traces(marker=dict(size=10))
    return fig

# Sentiment
analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text, rating):
    if rating == 5:
        return "Positive"
    sentiment_score = analyzer.polarity_scores(text)
    return "Positive" if sentiment_score['compound'] > 0 else "Negative"

# Kesimpulan
def generate_summary(df):
    total_reviews = len(df)
    if total_reviews == 0:
        return "Tidak ada data ulasan untuk dianalisis."
    average_rating = df["Star Given"].mean()
    most_common_rating = df["Star Given"].mode().iloc[0] if not df["Star Given"].mode().empty else "N/A"
    df_monthly_avg = df.groupby(df['Publish Date'].dt.to_period('M'))['Star Given'].mean().reset_index()
    df_monthly_avg['Publish Date'] = df_monthly_avg['Publish Date'].astype(str)
    trend_summary = ""
    if len(df_monthly_avg) > 1:
        first_avg = df_monthly_avg.iloc[0]['Star Given']
        last_avg = df_monthly_avg.iloc[-1]['Star Given']
        if last_avg > first_avg:
            trend_summary = f"Tren rating meningkat dari **{first_avg:.2f}** ke **{last_avg:.2f}**."
        elif last_avg < first_avg:
            trend_summary = f"Tren rating menurun dari **{first_avg:.2f}** ke **{last_avg:.2f}**."
        else:
            trend_summary = "Tren rating stabil."
    return f"""
    ### 📝 Kesimpulan Analisis Ulasan

    - Total ulasan: **{total_reviews}**
    - Rata-rata rating: **{average_rating:.2f} dari 5**
    - Rating paling umum: **{most_common_rating}**
    - {trend_summary}
    """

# Insight
def generate_insight_from_data(df):
    common_words = most_common_words(df["Review Text"])
    keywords = ", ".join(common_words['Kata'].head(5))
    sentiment_count = df['Sentiment'].value_counts()
    pos = sentiment_count.get("Positive", 0)
    neg = sentiment_count.get("Negative", 0)
    return f"""
    ### 📌 Highlight Review

    Dari total **{len(df)} ulasan**:  
    - **{pos} positif**  
    - **{neg} negatif**

    Kata populer: **{keywords}**
    """

# MAIN APP
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = df.dropna(subset=["Review Text", "Star Given"])
    df["Review Text"] = df["Review Text"].astype(str)
    df["Star Given"] = pd.to_numeric(df["Star Given"], errors="coerce")
    df["Publish Date"] = pd.to_datetime(df["Publish Date"], errors='coerce')
    df = df.dropna(subset=["Star Given", "Publish Date"])
    df["Star Given"] = df["Star Given"].astype(int)
    df["Sentiment"] = df.apply(lambda row: get_sentiment(row["Review Text"], row["Star Given"]), axis=1)

    # Filter
    st.sidebar.header("🎛️ Filter")
    rating = st.sidebar.slider("Filter Rating", 1, 5, (1, 5))
    keyword = st.sidebar.text_input("🔍 Kata kunci (opsional)")
    filtered_df = df[(df["Star Given"] >= rating[0]) & (df["Star Given"] <= rating[1])]
    if keyword:
        filtered_df = filtered_df[filtered_df["Review Text"].str.contains(keyword, case=False, na=False)]

    st.success(f"✨ Ditemukan **{len(filtered_df)}** ulasan setelah filter")

    # Visualisasi
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_rating_plot(filtered_df), use_container_width=True)
    with col2:
        st.plotly_chart(create_monthly_trend(filtered_df), use_container_width=True)

    st.divider()
    st.markdown(generate_summary(filtered_df))
    st.markdown("### 🔠 Kata Paling Sering Muncul")
    st.bar_chart(most_common_words(filtered_df["Review Text"]).set_index("Kata"))

    # Tabel opsional
    if st.sidebar.checkbox("📋 Tampilkan Tabel", value=True):
        st.markdown("### 🧾 Tabel Ulasan")
        st.dataframe(filtered_df[["Reviewer Name", "Publish Date", "Star Given", "Review Text", "Sentiment"]], use_container_width=True)

    st.markdown(generate_insight_from_data(filtered_df))

    # Unduh hasil
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Unduh Data Filtered (CSV)", csv, "filtered_reviews.csv", "text/csv")
else:
    st.info("⬆️ Upload file CSV dengan kolom: Reviewer Name, Review Text, Star Given, Publish Date.")

    
