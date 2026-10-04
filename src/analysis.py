"""Analysis interfaces for Premier League project."""

from typing import Any
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def _not_ready() -> None:
    raise NotImplementedError("Analysis is outside Day 1 scope.")

def analyze_home_advantage(df: pd.DataFrame) -> pd.Series:
    """
    RQ1: Tính tỷ lệ thắng/hòa/thua và vẽ biểu đồ Bar chart chứng minh lợi thế sân nhà.
    """
    # Chọn cột nhãn kết quả (ưu tiên 'result_label', nếu không có thì dùng 'FTR')
    col_name = 'result_label' if 'result_label' in df.columns else 'FTR'
    
    # Tính toán phần trăm
    total_matches = len(df)
    results_count = df[col_name].value_counts()
    win_rates = (results_count / total_matches) * 100
    
    # Thiết lập và vẽ biểu đồ Bar chart
    plt.figure(figsize=(8, 5))
    ax = sns.barplot(x=win_rates.index, y=win_rates.values, hue=win_rates.index, palette='mako', legend=False)
    
    plt.title('Phân tích Lợi thế Sân nhà tại Premier League', fontsize=14, pad=15)
    plt.ylabel('Tỷ lệ phần trăm (%)', fontsize=12)
    plt.xlabel('Kết quả', fontsize=12)
    
    # Ghi chú số phần trăm lên đầu mỗi cột
    for i, v in enumerate(win_rates.values):
        ax.text(i, v + 1, f'{v:.1f}%', ha='center', fontweight='bold')
        
    # Tạo thư mục và xuất file ảnh
    os.makedirs('charts', exist_ok=True)
    plt.tight_layout()
    plt.savefig('charts/home_advantage_bar.png', dpi=300)
    plt.close()
    
    return win_rates

def analyze_team_performance(data: Any) -> Any:
    """Reserve RQ2 analysis."""
    _not_ready()

def analyze_goal_distribution(data: Any) -> Any:
    """Reserve RQ4 analysis."""
    _not_ready()

def analyze_halftime_fulltime(data: Any) -> Any:
    """Reserve RQ3 analysis."""
    _not_ready()

def analyze_match_statistics(data: Any) -> Any:
    """Reserve RQ5 analysis."""
    _not_ready()