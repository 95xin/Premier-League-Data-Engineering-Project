import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import time



# general request function, with exception handling and fake header
def get_soup(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
    }
    try:
        page = requests.get(url, headers=headers, timeout=10)
        page.raise_for_status()
        page.encoding = 'utf-8'
        soup = BeautifulSoup(page.text, "html.parser")
        return soup
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None




# scrape daily latest data
def league_table():
    url = 'https://www.bbc.co.uk/sport/football/premier-league/table'
    soup = get_soup(url)
    if soup is None:
        return pd.DataFrame()

    # find all tables
    tables = soup.find_all('table')

    for table in tables:
        # check if it's the correct table (first row title contains 'Team' word)
        headers = [th.text for th in table.find_all('th')]
        if 'Team' in headers:
            print("Found the correct league table!")
            league_table = pd.DataFrame(columns=headers)
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                data = [col.text.strip() for col in cols]
                if data:
                    league_table.loc[len(league_table)] = data
            league_table = league_table.drop(columns=[col for col in league_table.columns if 'Form' in col], errors='ignore')
            return league_table

    print("No matching league table found.")
    return pd.DataFrame()









def detail_top():
    url = 'https://www.worldfootball.net/goalgetter/eng-premier-league-2024-2025/'
    soup = get_soup(url)
    if soup is None:
        return pd.DataFrame()

    table = soup.find("table", class_="standard_tabelle")
    if table is None:
        print("Detail top scorer table not found.")
        return pd.DataFrame()

    headers = [th.text for th in table.find_all('th')]
    detail_top_scorer = pd.DataFrame(columns=headers)

    for j in table.find_all('tr')[1:]:
        row_data = j.find_all('td')
        row = [i.text for i in row_data]
        if row:
            detail_top_scorer.loc[len(detail_top_scorer)] = row

    detail_top_scorer = detail_top_scorer.drop([''], axis=1, errors='ignore')
    if 'Team' in detail_top_scorer.columns:
        detail_top_scorer.Team = detail_top_scorer.Team.str.replace('\n\n', '')
    if 'Goals (Penalty)' in detail_top_scorer.columns:
        detail_top_scorer['Penalty'] = detail_top_scorer['Goals (Penalty)'].str.extract(r'\((\d+)\)')[0]
        detail_top_scorer['Goals (Penalty)'] = detail_top_scorer['Goals (Penalty)'].str.extract(r'^(\d+)')[0]
        detail_top_scorer.rename(columns={'Goals (Penalty)':'Goals'}, inplace=True)

    detail_top_scorer = detail_top_scorer.drop(['#'], axis=1, errors='ignore')
    return detail_top_scorer




def player_table():
    urls = [f'https://www.worldfootball.net/players_list/eng-premier-league-2024-2025/nach-name/{i:d}' for i in range(1, 12)]
    header = ['Player','','Team','born','Height','Position']
    df = pd.DataFrame(columns=header)

    def player(ev):
        soup = get_soup(ev)
        if soup is None:
            return pd.DataFrame()
        table = soup.find("table", class_="standard_tabelle")
        if table is None:
            return pd.DataFrame()

        headers = [th.text for th in table.find_all('th')]
        players = pd.DataFrame(columns=headers)

        for j in table.find_all('tr')[1:]:
            row_data = j.find_all('td')
            row = [i.text for i in row_data]
            if row:
                players.loc[len(players)] = row
        return players

    for url in urls:
        a = player(url)
        df = pd.concat([df, a], axis=0, ignore_index=True)
        time.sleep(1)

    df = df.drop([''], axis=1, errors='ignore')
    return df




def all_time_table():
    url = 'https://www.worldfootball.net/alltime_table/eng-premier-league/pl-only/'
    soup = get_soup(url)
    if soup is None:
        return pd.DataFrame()

    table = soup.find("table", class_="standard_tabelle")
    if table is None:
        print("All time table not found.")
        return pd.DataFrame()

    headers = ['pos','#','Team','Matches','wins','Draws','Losses','Goals','Dif','Points']
    alltime_table = pd.DataFrame(columns=headers)

    for j in table.find_all('tr')[1:]:
        row_data = j.find_all('td')
        row = [i.text for i in row_data]
        if row:
            alltime_table.loc[len(alltime_table)] = row

    alltime_table = alltime_table.drop(['#'], axis=1, errors='ignore')
    if 'Team' in alltime_table.columns:
        alltime_table.Team = alltime_table.Team.str.replace('\n', '')
    return alltime_table




def all_time_winner_club():
    url = 'https://www.worldfootball.net/winner/eng-premier-league/'
    soup = get_soup(url)
    if soup is None:
        return pd.DataFrame()

    table = soup.find("table", class_="standard_tabelle")
    if table is None:
        print("All time winner table not found.")
        return pd.DataFrame()

    headers = [th.text for th in table.find_all('th')]
    winners = pd.DataFrame(columns=headers)

    for j in table.find_all('tr')[1:]:
        row_data = j.find_all('td')
        row = [i.text for i in row_data]
        if row:
            winners.loc[len(winners)] = row

    winners = winners.drop([''], axis=1, errors='ignore')
    winners['Year'] = winners['Year'].str.replace('\n', '')
    return winners




def top_scorers_seasons():
    url = 'https://www.worldfootball.net/top_scorer/eng-premier-league/'
    soup = get_soup(url)
    if soup is None:
        return pd.DataFrame()

    table = soup.find("table", class_="standard_tabelle")
    if table is None:
        print("Top scorers per season table not found.")
        return pd.DataFrame()

    headers = ['Season','#','Top scorer','#','Team','goals']
    winners = pd.DataFrame(columns=headers)

    for j in table.find_all('tr')[1:]:
        row_data = j.find_all('td')
        row = [i.text for i in row_data]
        if row:
            winners.loc[len(winners)] = row

    winners = winners.drop(['#'], axis=1, errors='ignore')
    winners = winners.replace('\\n','',regex=True).astype(str)
    winners['Season'] = winners['Season'].replace('', np.nan).ffill()
    return winners




def goals_per_season():
    url = 'https://www.worldfootball.net/stats/eng-premier-league/1/'
    soup = get_soup(url)
    if soup is None:
        return pd.DataFrame()

    table = soup.find("table", class_="standard_tabelle")
    if table is None:
        print("Goals per season table not found.")
        return pd.DataFrame()

    headers = [th.text for th in table.find_all('th')]
    goals_per_season = pd.DataFrame(columns=headers)

    for j in table.find_all('tr')[1:]:
        row_data = j.find_all('td')
        row = [i.text for i in row_data]
        if row:
            goals_per_season.loc[len(goals_per_season)] = row

    goals_per_season.drop(goals_per_season.index[-1], inplace=True, errors='ignore')
    goals_per_season = goals_per_season.drop(['#'], axis=1, errors='ignore')
    goals_per_season.rename(columns={'goals':'Goals','\u00d8 goals':'Average Goals'}, inplace=True)

    return goals_per_season




def top_scorers():
    url = 'https://www.bbc.co.uk/sport/football/premier-league/top-scorers'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, 'html.parser')

    # scrape names and clubs
    names = [div.text.strip() for div in soup.select("div[class*='PlayerName']")]
    clubs = [div.text.strip() for div in soup.select("div[class*='TeamsSummary']")]

    # remove duplicates (each person appears twice in the web structure)
    names = names[::2]
    clubs = clubs[::2]

    if len(names) != len(clubs):
        print("Mismatch in name and club counts!")
        return pd.DataFrame()

    # build DataFrame
    df = pd.DataFrame({
        "Name": names,
        "Club": clubs
    })

    return df






