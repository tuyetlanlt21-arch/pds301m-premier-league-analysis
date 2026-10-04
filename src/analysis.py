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

def analyze_team_performance(df: pd.DataFrame) -> pd.Series:
    """
    RQ2: Tính tổng số bàn thắng của từng đội và vẽ biểu đồ Top 10 đội ghi bàn nhiều nhất.
    """
    # Tính tổng bàn thắng khi đá sân nhà và sân khách
    home_goals = df.groupby('HomeTeam')['FTHG'].sum().reset_index()
    home_goals.columns = ['Team', 'Goals']
    
    away_goals = df.groupby('AwayTeam')['FTAG'].sum().reset_index()
    away_goals.columns = ['Team', 'Goals']
    
    # Gộp lại để lấy tổng toàn giải
    total_goals = pd.concat([home_goals, away_goals]).groupby('Team')['Goals'].sum().sort_values(ascending=False)
    
    # Vẽ biểu đồ Bar chart nằm ngang cho Top 10
    plt.figure(figsize=(10, 6))
    sns.barplot(x=total_goals.head(10).values, y=total_goals.head(10).index, hue=total_goals.head(10).index, palette='viridis', legend=False)
    
    plt.title('Top 10 Đội Ghi Nhiều Bàn Thắng Nhất', fontsize=14, pad=15)
    plt.xlabel('Tổng số bàn thắng', fontsize=12)
    plt.ylabel('Đội bóng', fontsize=12)
    
    os.makedirs('charts', exist_ok=True)
    plt.tight_layout()
    plt.savefig('charts/top_scoring_teams.png', dpi=300)
    plt.close()
    
    return total_goals

def analyze_goal_distribution(df: pd.DataFrame) -> None:
    """
    RQ4: Vẽ biểu đồ Histogram phân bố tổng số bàn thắng trong các trận đấu.
    """
    # Tạo cột tổng bàn thắng nếu chưa có
    if 'total_goals' not in df.columns:
        df['total_goals'] = df['FTHG'] + df['FTAG']
        
    plt.figure(figsize=(8, 5))
    sns.histplot(df['total_goals'], bins=range(0, int(df['total_goals'].max()) + 2), kde=True, color='teal')
    
    plt.title('Phân bố Tổng số Bàn thắng mỗi Trận đấu', fontsize=14, pad=15)
    plt.xlabel('Tổng số bàn thắng', fontsize=12)
    plt.ylabel('Số lượng trận đấu', fontsize=12)
    plt.xticks(range(0, int(df['total_goals'].max()) + 1))
    
    os.makedirs('charts', exist_ok=True)
    plt.tight_layout()
    plt.savefig('charts/goal_distribution_hist.png', dpi=300)
    plt.close()

def analyze_halftime_fulltime(df: pd.DataFrame) -> pd.DataFrame:
    """
    RQ3: Phân tích mối liên hệ giữa kết quả hiệp 1 (HTR) và kết quả chung cuộc (FTR).
    """
    # Lập bảng chéo đếm số lượng trận đấu (H: Home, D: Draw, A: Away)
    ht_ft_crosstab = pd.crosstab(df['HTR'], df['FTR'], 
                                 rownames=['Half-Time (HTR)'], 
                                 colnames=['Full-Time (FTR)'])
    
    # Sắp xếp lại thứ tự cột/hàng cho chuẩn (Home, Draw, Away)
    order = ['H', 'D', 'A']
    ht_ft_crosstab = ht_ft_crosstab.reindex(index=order, columns=order)
    
    plt.figure(figsize=(7, 5))
    sns.heatmap(ht_ft_crosstab, annot=True, fmt='d', cmap='Blues')
    
    plt.title('Mối liên hệ giữa Kết quả Hiệp 1 và Chung cuộc', fontsize=14, pad=15)
    
    os.makedirs('charts', exist_ok=True)
    plt.tight_layout()
    plt.savefig('charts/halftime_fulltime_heatmap.png', dpi=300)
    plt.close()
    
    return ht_ft_crosstab

def analyze_match_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    RQ5: Vẽ Heatmap thể hiện mức độ tương quan giữa các chỉ số thống kê trong trận.
    """
    # Gộp các chỉ số sân nhà và sân khách để phân tích tổng thể
    stats_df = pd.DataFrame()
    stats_df['Tổng Bàn thắng'] = df['FTHG'] + df['FTAG']
    stats_df['Tổng Cú sút'] = df['HS'] + df['AS']
    stats_df['Sút trúng đích'] = df['HST'] + df['AST']
    stats_df['Phạt góc'] = df['HC'] + df['AC']
    stats_df['Phạm lỗi'] = df['HF'] + df['AF']
    
    # Tính ma trận tương quan (Pearson correlation)
    corr_matrix = stats_df.corr()
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, fmt='.2f')
    
    plt.title('Ma trận Tương quan giữa các Chỉ số Thống kê', fontsize=14, pad=15)
    
    os.makedirs('charts', exist_ok=True)
    plt.tight_layout()
    plt.savefig('charts/match_stats_correlation.png', dpi=300)
    plt.close()
    
    return corr_matrix