
from production_engine import optimize_coupon_logic

def test_opt():
    # 6 legs, 10 horses each, scores 0.1 to 0.01
    legs_data = [[(f"H{i}_{j}", 0.1/(j+1)) for j in range(10)] for i in range(6)]
    selection, cost = optimize_coupon_logic(legs_data, 700.0)
    
    print(f"Cost: {cost}")
    for i, sel in enumerate(selection):
        print(f"Leg {i}: {len(sel)} horses")

if __name__ == "__main__":
    test_opt()
