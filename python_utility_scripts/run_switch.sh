START_TIME=$SECONDS
python -m switch_mod.solve -v --solver=gurobi
ELAPSED_TIME=$(($SECONDS - $START_TIME))
echo "Switch took $ELAPSED_TIME seconds"
