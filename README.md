Run script 1 (browse/write) for 10 minutes:
PERF_USERS=100 PERF_DURATION=600 SIMULATION_CLASS=youtrack.UC01_createOrUpdate run.sh

Run script 2 (search) for 10 minutes:
PERF_USERS=100 PERF_DURATION=60 SIMULATION_CLASS=youtrack.UC02_performSearches run.sh
