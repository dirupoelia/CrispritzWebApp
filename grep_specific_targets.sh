#$1 is bulge_t, 2 is bulge_s, 3 is mms, 4 is first char guide, 5 is second char guide, 6 is job_id

echo 'a'
grep -P '^'$1'\t'$4'[-,'$5'].*\t'$3'\t'$2'' Results/$6/$6.targets.txt > example_todo_delete$1$2$3$4.txt 
echo 'Done'
(head -n1 Results/$6/$6.targets.txt && cat example_todo_delete$1$2$3$4.txt) > filename1 && mv filename1 example_todo_delete$1$2$3$4.txt
