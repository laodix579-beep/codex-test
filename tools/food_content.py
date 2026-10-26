"""C05 source labels and four existing website entrance IDs.

Raw uploaded JSONs keep their six semantic subcategories and original IDs.
The existing UI uses four entrance slots; only the lexical word is practised.
"""
UI_SUBCATEGORIES = {f'C05-W{i:02}': f'C05-S{i:02}' for i in range(1, 5)}
STUDY_WORDS = {'C05-S06-024': 'cold'}

def study_word(row):
    return STUDY_WORDS.get(row['id'], row['english'])
