.
#!/bin/bash
# set -o monitor

#Arguments
SEQMIN=11
SEQMAX=33
PARA=6 # How many to allow running at a time

#Init vars
njobs=0
count=0
for i in `seq ${SEQMIN} ${SEQMAX}`
do
   while [ "$njobs" -ge "${PARA}" ]
   do
      echo -n .
      sleep 0.4 # Sleep-wait cycle
      njobs=`jobs -p | wc -l`
   done
   echo

   ((njobs++))
   # Here you launch your job, ending with an ampersand to background it
   sleep 2 & # Run the job. "sleep 2" to simulate a 2 second process
   ((count++))
   echo Spawned task number $count : sequence $i

done

echo $count jobs spawned in total.
echo $njobs still running.
echo -n Final wait...
wait
echo done
