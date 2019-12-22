# Process csv files for Fleiss' Kappa

import csv
# Download from https://github.com/Shamya/FleissKappa
from fleiss import fleissKappa

tag_dict = {}
key_num = 0
result = []
with open('gold_standard.csv', newline='') as csvfile:
    files = csv.reader(csvfile)
    for row in files:
        row_result = [0] * 8
        cells = row[-4:-1]
        for cell in cells:
            if cell not in tag_dict and cell not in ['Micaela', 'Shantina', 'Danyi']:
                tag_dict[cell] = key_num
                key_num += 1
            if cell not in ['Micaela', 'Shantina', 'Danyi']:
                row_result[tag_dict[cell]] += 1
        result.append(row_result)
result = result[1:]
kappa = fleissKappa(result, 3)
