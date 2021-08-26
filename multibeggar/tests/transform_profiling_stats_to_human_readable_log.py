import pstats
import os

with open(os.path.join(os.getcwd(), 'output', 'multibeggar_use.py.profile.log'), 'w') as out_file:
    p = pstats.Stats(os.path.join(os.getcwd(), 'output', 'multibeggar_use.py.stats'), stream=out_file)
    p.sort_stats('cumulative').print_stats()
