import cProfile
import pstats
import multibeggar_use

cProfile.run("multibeggar_use.multibeggar_use()", filename="multibeggar_use.prof")
with open("multibeggar_use.prof.log", "w", encoding="utf-8") as output_file:
    stats = pstats.Stats("multibeggar_use.prof", stream=output_file)
    stats.sort_stats("cumulative").print_stats()
