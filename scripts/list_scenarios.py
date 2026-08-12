from app.scenarios import load_scenarios

for scenario in load_scenarios().values():
    print(f"{scenario.id:28} {scenario.title}")
