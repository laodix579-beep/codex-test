"""C06 raw six semantic groups map into the existing four website entrances."""
UI_SUBCATEGORIES = {f'C06-W{i:02}': f'C06-S{i:02}' for i in range(1, 5)}

def study_word(row):
    return row['english']
