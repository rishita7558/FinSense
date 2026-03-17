import plotly.express as px
import pandas as pd

def create_timeline_chart(data):
    df = pd.DataFrame(data)
    
    if df.empty:
        return px.scatter(title="No timeline data available.")

    # Sort strictly by time so graph plots chronologically
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values(by="time")

    fig = px.scatter(
        df,
        x="time",
        y="risk_score",
        color="emotion",
        hover_data=["entities", "risk_level"],
        title="Financial Risk & Emotion over Time",
        labels={"time": "Date/Time", "risk_score": "Risk Score", "emotion": "Emotion"}
    )
    
    # Make the scatter dots big and connected with a faint line so it looks like a timeline
    fig.update_traces(mode='lines+markers', marker=dict(size=14, line=dict(width=2, color='DarkSlateGrey')))
    fig.update_layout(xaxis_title="Time of Recording", yaxis_title="Computed Financial Risk")

    return fig