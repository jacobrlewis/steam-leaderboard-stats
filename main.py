import requests
import xml.etree.ElementTree as ET
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Rivals 2, ranked lite ids
GAME_ID = '2217000'
LEADERBOARDS = {
    'ranked-lite': '14800950',
    'spring-2025': '16200142',
    'summer-2025': '16915072',
    'fall-2025': '17834843',
    'winter-2026': '18722539',
    'spring-2026': '19096871'
}

def get_df_cache_name(leaderboard: str):
    return f'./cache/{leaderboard}/df.pkl'

def get_xml_cache_name(leaderboard: str):
    return f'./cache/{leaderboard}/xml'

def download_xml(leaderboard: str):
    """
    Download and save each xml file provided by the steam xml api
    """
    next_url = f'https://steamcommunity.com/stats/{GAME_ID}/leaderboards/{leaderboard}/?xml=1'

    while next_url is not None:
        xml_raw = requests.get(next_url).text
        xml = ET.fromstring(xml_raw)
        
        start = xml.find('entryStart').text.strip()
        end = xml.find('entryEnd').text.strip()

        with open(f'{get_xml_cache_name(leaderboard)}/{start}-{end}.xml', 'w') as file:
            file.write(xml_raw)
            print(f'saved {file.name}')
        
        next_url = xml.find("nextRequestURL").text.strip() if xml.find("nextRequestURL") is not None else None


def get_leaderboard_xml(leaderboard: str):
    """
    If leaderboard xml cache does not exist, download it
    """
    os.makedirs(os.path.dirname(get_xml_cache_name(leaderboard)), exist_ok=True)
    if len(os.listdir(get_xml_cache_name(leaderboard))) == 0:
        download_xml(leaderboard)


def xml_to_df(leaderboard: str):
    """
    Return a dataframe of leaderboard entrants from all xml files
    """
    get_leaderboard_xml(leaderboard)

    all_dfs = []
    for file_name in os.listdir(get_xml_cache_name(leaderboard)):
        file_path = os.path.join(get_xml_cache_name(leaderboard), file_name)
        df = pd.read_xml(file_path, xpath='.//entry')
        all_dfs.append(df)

    return pd.concat(all_dfs, ignore_index=True)


def get_leaderboard_df(leaderboard: str):
    """
    Find the leaderboard df in cache, or create a new one
    """
    df_cache_name = get_df_cache_name(leaderboard)
    if os.path.exists(df_cache_name):
        return pd.read_pickle(df_cache_name)

    df = xml_to_df(leaderboard)
    df.to_pickle(df_cache_name)
    print(f'saved {df_cache_name}')
    return df


def rivals2_plot(combined_df: pd.DataFrame, name):
    """
    Creates a rank histogram specific to Rivals of Aether II ranked lite
    """
    bin_edges = [0, 500, 700, 900, 1100, 1300, 1500, combined_df['score'].max() + 1]
    bin_labels = ['Stone', 'Bronze', 'Silver', 'Gold', 'Plat', 'Diamond', 'Master']
    colors = ['#A9A9A9', '#CD7F32', '#C0C0C0', '#FFD700', '#E5E4E2', '#00BFFF', '#98FB98']

    # Create a new labels list that includes the bin ranges
    custom_labels = ['Stone 0-499', 'Bronze 500-699', ' Silver 700-899', 'Gold 900-1099', 'Plat 1100-1299', 'Diamond 1300-1499', 'Master 1500+']

    # Categorize the scores into the custom bins
    ranked_bins = pd.cut(combined_df['score'], bins=bin_edges, labels=bin_labels, right=False)

    # Count the number of entries in each rank bin
    rank_counts = ranked_bins.value_counts().reindex(bin_labels)

    # Calculate the total number of players
    total_players = rank_counts.sum()

    # Plotting
    plt.figure(figsize=(10, 8))
    bars = rank_counts.plot(kind='bar', color=colors, edgecolor='black')
    plt.xlabel('Rank')
    plt.ylabel('Number of Players')
    plt.title(f'Rivals II Rank Distribution - {name} - {datetime.today().strftime('%Y-%m-%d')} - {total_players:,} total players')

    # Rotate x-tick labels for better readability
    plt.xticks(ticks=range(len(custom_labels)), labels=custom_labels, rotation=45)

    # Annotate each bar with percentage
    for bar in bars.patches:
        height = bar.get_height()
        percentage = (height / total_players) * 100
        plt.text(bar.get_x() + bar.get_width() / 2, height, f'{percentage:.1f}%', 
                ha='center', va='bottom')

    plt.text(.06, .05, 'By Sixbux\nhttps://github.com/jacobrlewis/steam-leaderboard-stats', fontsize=10, transform=plt.gcf().transFigure)    
    
    # Save the plot
    plt.tight_layout()  # Adjust layout to make room for the x-axis labels
    plt.savefig(f'rank_distribution-{name}.png', format="png", dpi=300)
    plt.close()


if __name__ == '__main__':
    for name, leaderboard in LEADERBOARDS.items():
        df = get_leaderboard_df(leaderboard)
        rivals2_plot(df, name)
