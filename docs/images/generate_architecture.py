import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_architecture():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Define positions
    positions = {
        "Client": (1, 6),
        "Gateway": (4, 6),
        "Redis": (4, 4),
        "Queue": (7, 6),
        "Database": (7, 4),
        "AI Service": (10, 4),
        "Prometheus": (4, 2),
        "Grafana": (7, 2)
    }

    # Define box style
    box_props = dict(boxstyle='round,pad=0.5', facecolor='#e0f7fa', edgecolor='#006064')
    
    # Draw Nodes
    for name, (x, y) in positions.items():
        ax.text(x, y, name, ha='center', va='center', size=12, bbox=box_props)

    # Define Arrows
    arrows = [
        ("Client", "Gateway", "HTTP Request"),
        ("Gateway", "Redis", "Rate Limit Check"),
        ("Gateway", "Queue", "Async Log"),
        ("Queue", "Database", "Batch Insert"),
        ("Database", "AI Service", "Analyze Incidents"),
        ("Gateway", "Prometheus", "Expose Metrics"),
        ("Prometheus", "Grafana", "Visualization")
    ]

    # Draw Arrows
    for start, end, label in arrows:
        start_x, start_y = positions[start]
        end_x, end_y = positions[end]
        
        # Calculate arrow midpoints for labels
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        
        ax.annotate("", xy=(end_x, end_y), xytext=(start_x, start_y),
                    arrowprops=dict(arrowstyle="->", lw=2, color='black'))
        ax.text(mid_x, mid_y + 0.2, label, ha='center', va='bottom', fontsize=9, color='blue')

    plt.title("SentinelStack Architecture", fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig("d:/Rajat/Projects/SENTINELSTACK/docs/images/architecture.png", dpi=300)
    print("Architecture diagram saved to docs/images/architecture.png")

if __name__ == "__main__":
    draw_architecture()
