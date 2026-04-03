"""Bar plot: iterations per question per model per run."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

base = r"d:\Rancho\projects\2409 - Pistoia\tasks\2603-01 - rerun 5\LLM\notebooks\artifacts\evaluation_results\rerun-2026"
df = pd.read_excel(f"{base}\\05-Q3-iterations.xlsx")

# Shorten model names for display
df['model_short'] = df['model'].map({
    'claude-sonnet-4-6 (20it)': 'Sonnet 4.6\n(20 iter)',
    'claude-sonnet-4-6 (100it)': 'Sonnet 4.6\n(100 iter)',
    'gpt-5.2 (20it)': 'GPT-5.2\n(20 iter)',
    'gpt-5.2 (100it)': 'GPT-5.2\n(100 iter)',
})

questions = ['TDP-43, ALS', 'TDP-43, cancer', 'BRAF, melanoma']
q_labels = ['Q1: TDP-43 / ALS', 'Q2: TDP-43 / Cancer\n(animal models)', 'Q3: BRAF / Melanoma\n(clinical evidence)']
models = ['Sonnet 4.6\n(20 iter)', 'Sonnet 4.6\n(100 iter)', 'GPT-5.2\n(20 iter)', 'GPT-5.2\n(100 iter)']
colors = ['#E07850', '#A03020', '#A0A0A0', '#505050']

fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)

for qi, (q, q_label) in enumerate(zip(questions, q_labels)):
    ax = axes[qi]
    q_data = df[df['question'] == q]

    x = np.arange(10)  # 10 runs
    width = 0.2
    offsets = [-1.5, -0.5, 0.5, 1.5]

    for mi, (model, color, offset) in enumerate(zip(models, colors, offsets)):
        m_data = q_data[q_data['model_short'] == model].sort_values('run')
        if len(m_data) > 0:
            bars = ax.bar(x + offset * width, m_data['iterations'].values, width,
                         label=model if qi == 0 else '', color=color, alpha=0.85, edgecolor='white', linewidth=0.5)

    ax.set_title(q_label, fontsize=13, fontweight='bold')
    ax.set_xlabel('Run', fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels([str(i) for i in range(10)])
    ax.grid(axis='y', alpha=0.3)
    ax.set_axisbelow(True)

    ax.set_ylim(0, 100)
    if qi == 0:
        ax.set_ylabel('Iterations', fontsize=12)

    # Add horizontal line at 20 (iteration cap for 20it runs)
    ax.axhline(y=20, color='red', linestyle='--', alpha=0.4, linewidth=1)
    ax.text(9.5, 21, 'cap=20', color='red', alpha=0.5, fontsize=8, ha='right')

handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='upper center', ncol=4, fontsize=10, bbox_to_anchor=(0.5, 1.02),
           frameon=True, fancybox=True, shadow=True)

plt.tight_layout(rect=[0, 0, 1, 0.93])

out_path = f"{base}\\05-Q3-iterations-barplot.png"
plt.savefig(out_path, dpi=150, bbox_inches='tight')
print(f"Saved to {out_path}")
plt.close()
