def optimize_coupon_smart(legs_data, budget_tl, unit=1.25):
    """
    Smart Optimization: Balances Risk vs Budget based on Field Size & Entropy.
    """
    # 1. Analyze Each Leg
    leg_configs = []
    
    for i, leg in enumerate(legs_data):
        field_size = len(leg)
        scores = [x[1] for x in leg]
        top_score = scores[0] if scores else 0
        gap = (scores[0] - scores[1]) if len(scores)>1 else 0.5
        
        # Determine Race Difficulty (Entropy)
        difficulty = "NORMAL"
        if field_size >= 12 and top_score < 0.35: difficulty = "HARD"
        elif field_size <= 7 or top_score > 0.60: difficulty = "EASY"
        
        # Set Min/Max Selection Constraints
        min_sel = 1
        max_sel = int(field_size * 0.5) # Cap at 50% of field
        
        if difficulty == "HARD":
            min_sel = 4  # Force verify wider cover in chaos
        elif difficulty == "NORMAL":
            min_sel = 2
        else: # EASY
            min_sel = 1 # Allow Banko
            
        # Refine Banko Rule: Even in Hard races, if we really have no budget, we might need a risk
        # But initially, try to respect the classification.
        
        # Special Case: Monster Favorite
        if top_score > 0.85: min_sel = 1
        
        leg_configs.append({
            'min': min_sel,
            'max': max(min_sel, max_sel),
            'candidates': leg
        })
        
    # 2. Greedy Allocation with Constraints
    current_selection = [l['candidates'][:l['min']] for l in leg_configs]
    
    while True:
        best_gain = -1
        best_leg = -1
        
        # Current Cost
        c_comb = 1
        for s in current_selection: c_comb *= len(s)
        current_cost = c_comb * unit
        
        # Try adding next horse to each leg
        for i, config in enumerate(leg_configs):
            curr_len = len(current_selection[i])
            
            # Check Max Constraint
            if curr_len >= config['max'] or curr_len >= len(config['candidates']):
                continue
                
            next_horse = config['candidates'][curr_len]
            
            # Marginal Cost Increase
            # New count = curr_len + 1
            # Multiplier increase factor = (L+1)/L
            mult_factor = (curr_len + 1) / curr_len
            new_cost = current_cost * mult_factor
            
            if new_cost <= budget_tl:
                # Heuristic: Value = Score of added horse
                # We can also weight it by "Need": Adding 3rd horse to Hard race > 5th to Easy race
                gain = next_horse[1]
                
                # Bonus for "Hard" races if under-covered
                if curr_len < 4 and len(config['candidates']) > 12:
                    gain *= 1.2
                    
                if gain > best_gain:
                    best_gain = gain
                    best_leg = i
        
        if best_leg != -1:
            next_h = leg_configs[best_leg]['candidates'][len(current_selection[best_leg])]
            current_selection[best_leg].append(next_h)
        else:
            break
            
    final_c = 1
    for s in current_selection: final_c *= len(s)
    return current_selection, final_c * unit
