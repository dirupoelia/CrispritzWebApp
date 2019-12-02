#$1 is bulge_type, 2 is bulge_size, 3 is mms, 4 is first char guide, 5 is second char guide, 6 is job_id, 7 is guide, 
# 8 is file to grep (eg 'targets.cluster' for ref search, 'targets.cluster.minmaxdisr' for var search)
cd Results/$6
grep -P '^'$1'\t'$4'[-,'$5'].*\t'$3'\t'$2'' $6.$8.txt > $6.$1$2$3.$7.txt 
echo 'Done'

#To insert header, atm is inserted when loaded into the app
#(head -n1 Results/$6/$6.targets.txt && cat example_todo_delete$1$2$3$4.txt) > filename1 && mv filename1 example_todo_delete$1$2$3$4.txt
