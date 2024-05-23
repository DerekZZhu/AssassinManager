import numpy as np

# CONSTANTS, CHANGE AS NECESSARY
FILEPATH = "kill_log.txt"
TEAMS = {
    "ML": [
        "Michael_Li", "Hari_Sethuraman", "Karim_Maftoun", "Kelsey_Sun"
    ],
    "Framework": [
        "Nathan_Li", "Eric_Bae", "Victor_Cheng", "Janani_Raghavan"
    ],
    "Database": [
        "Joshua_Jung", "Derek_Zhu", "Michael_Xu", "Cindy_Ni"
    ]
}
MAX_BONUS_STREAK = 5
IDX_TO_PLAYERS = [player for team in TEAMS.values() for player in team]
PLAYERS_TO_IDX = {player: idx for idx, player in enumerate(IDX_TO_PLAYERS)}

# Utility function to read the file
def read_names(file_path):
    list1 = []
    list2 = []
    with open(file_path, 'r') as file:
        for line in file:
            names = line.split()
            if len(names) >= 2:
                list1.append(names[0])
                list2.append(names[1])
    return list1, list2

# Read in data and initialize variables
killers, victims = read_names(FILEPATH)
kills = np.zeros(len(PLAYERS_TO_IDX))
deaths = np.zeros(len(PLAYERS_TO_IDX))
streaks = np.zeros(len(PLAYERS_TO_IDX))
points = np.zeros(len(PLAYERS_TO_IDX))

# Calculate scores over time
for killer, victim in zip(killers, victims):
    killer_idx = PLAYERS_TO_IDX.get(killer, -1)
    victim_idx = PLAYERS_TO_IDX.get(victim, -1)

    # Check validity of killer and victim
    if killer_idx == -1:
        print(f"Killer {killer} not found")
        exit()
    if victim_idx == -1:
        print(f"Victim {victim} not found")
        exit()
    
    # Get killer and victim data
    victim_streak = streaks[victim_idx]
    victim_deaths = deaths[victim_idx]
    killer_streak = streaks[killer_idx]
    killer_points = points[killer_idx]
    killer_kills = kills[killer_idx]

    # Save new data
    killer_add_points = min(killer_streak + 2, MAX_BONUS_STREAK) + (victim_streak + 2 if victim_streak >= 2 else 0)
    kills[killer_idx] += 1
    streaks[killer_idx] += 1
    points[killer_idx] += killer_add_points
    deaths[victim_idx] += 1
    streaks[victim_idx] = 0

# Print out player scores individually
print("PLAYER STATS:")
for player, idx in PLAYERS_TO_IDX.items():
    print(f"{player} - Kills: {kills[idx]}, Deaths: {deaths[idx]}, Points: {points[idx]}")

# Print out total stats per team
print("\nTEAM STATS:")
for team, players in TEAMS.items():
    team_kills = sum(kills[PLAYERS_TO_IDX[player]] for player in players)
    team_deaths = sum(deaths[PLAYERS_TO_IDX[player]] for player in players)
    team_points = sum(points[PLAYERS_TO_IDX[player]] for player in players)
    print(f"{team} - Kills: {team_kills}, Deaths: {team_deaths}, Points: {team_points}")
