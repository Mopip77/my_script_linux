#!/bin/bash

thisFilePath=$(cd `dirname $0`; pwd)
targetPath=$(cd $1; pwd)

updateFiles=( $("${thisFilePath}/filter.py" update) )
deleteFiles=( $("${thisFilePath}/filter.py" delete) )

for f in "${updateFiles[@]}"
do
	/usr/local/anaconda3/bin/jupyter nbconvert --to html --template full "${f}"
done

for f in "${deleteFiles[@]}"
do
	a="$( echo $f | cut -d '.' -f 1).html"
	if [ -e "$a" ]
	then
		rm "${a}"
	fi
done

"${thisFilePath}/category_generator.py" "${targetPath}"
