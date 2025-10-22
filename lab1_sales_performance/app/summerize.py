from transformers import pipeline

summarizer = pipeline("text-generation", model="google/flan-t5-small")

def summarize_df(df, question):
    if df.empty:
        return "No data found."
    preview = df.head(5).to_string()
    prompt = f"Question: {question}\nData preview:\n{preview}\nSummarize key insights in one sentence."
    res = summarizer(prompt, max_new_tokens=80)
    return res[0]['generated_text']
