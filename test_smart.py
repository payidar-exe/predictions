
import json
import pandas as pd
from smart_opt import optimize_coupon_smart

def test_on_real_data():
    # Load Real Data from daily_forecasts.sql (Just reusing the structure for simulation)
    # We need scores, which aren't in the SQL (only selected ones are).
    # Ah, wait. The SQL only has the *selected* horses. We don't have the full field scores in the SQL.
    # We must assume random scores or re-run the prediction script to get the full list.
    
    # Let's mock a "Hard" race and an "Easy" race based on the counts we saw.
    
    legs_data = []
    
    # Leg 1: Field 22 (Hard/Crowded)
    # Scores: Assume fav is 0.20, others close.
    l1 = [(f"L1_H{i}", 0.20 if i==0 else 0.15/(i+1) + 0.05) for i in range(22)]
    # Sort by score desc
    l1.sort(key=lambda x: x[1], reverse=True)
    legs_data.append(l1)
    
    # Leg 2: Field 30 (Very Hard)
    l2 = [(f"L2_H{i}", 0.18 if i==0 else 0.14/(i+1) + 0.05) for i in range(30)]
    l2.sort(key=lambda x: x[1], reverse=True)
    legs_data.append(l2)
    
    # Leg 3: Field 28 (Hard)
    l3 = [(f"L3_H{i}", 0.25 if i==0 else 0.10) for i in range(28)]
    l3.sort(key=lambda x: x[1], reverse=True)
    legs_data.append(l3)
    
    # Leg 4: Field 12 (Medium) - Strong Fav
    l4 = [(f"L4_H{i}", 0.65 if i==0 else 0.05) for i in range(12)]
    l4.sort(key=lambda x: x[1], reverse=True)
    legs_data.append(l4)

    # Leg 5: Field 18 (Medium/Hard)
    l5 = [(f"L5_H{i}", 0.30 if i==0 else 0.10) for i in range(18)]
    legs_data.append(l5)
    
    # Leg 6: Field 30 (Very Hard)
    l6 = [(f"L6_H{i}", 0.15 if i==0 else 0.05) for i in range(30)]
    legs_data.append(l6)
    
    print("--- Running Smart Opt ---")
    sel, cost = optimize_coupon_smart(legs_data, 800.0)
    
    print(f"Total Cost: {cost}")
    for i, s in enumerate(sel):
        print(f"Leg {i+1} (Field {len(legs_data[i])}): Selected {len(s)}")

if __name__ == "__main__":
    test_on_real_data()
