import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

def draw_donut_circle(score: float) -> plt.Figure:
    """
    Draw a donut circle based on the given score.

    Parameters:
    score (float): The score to be visualized in the donut circle.

    Returns:
    plt.Figure: The matplotlib figure object containing the donut circle.
    """
    # Normalize the score to the range -1 to 1 just in case!
    score = max(min(score, 1), -1)
    
    fig, ax = plt.subplots(figsize=(4, 4))  # Use a square figure to hold the circle

    # Base circle as background (the donut)
    base_circle = Wedge((0.5, 0.5), 0.4, 0, 360, width=0.1, facecolor='lightgrey')
    ax.add_artist(base_circle)

    # Color and extent of the fill based on the score
    color = 'green' if score >= 0 else 'red'
    extent = abs(score) * 360  # Full circle for score = 1 or -1

    # Create and add the filled portion of the circle (the colored part of the donut)
    filled_circle = Wedge((0.5, 0.5), 0.4, 0, extent, width=0.1, facecolor=color)
    ax.add_artist(filled_circle)

    # Add text in the center of the donut
    ax.text(0.5, 0.55, "News Sentiment Score:", horizontalalignment='center', verticalalignment='center', fontsize=9, fontweight='bold')
    ax.text(0.5, 0.45, f"{score:.2f}", horizontalalignment='center', verticalalignment='center', fontsize=12, fontweight='bold')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.axis('off')  # Turn off the axis

    return fig