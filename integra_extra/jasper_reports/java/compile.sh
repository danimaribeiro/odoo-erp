#!/bin/bash
#export JAVA_HOME=/opt/java/64/jdk1.7.0_25
if [ -z "$JAVA_HOME" ]; then
	directories="/usr/lib/jvm/java-6-sun-1.6.0.10/bin /usr/lib/j2sdk1.6-sun /usr/lib/j2sdk1.5-sun /opt/java/64/jdk1.7.0_45/bin"
	for d in $directories; do
		if [ -d "$d" ]; then
			export JAVA_HOME="$d"
		fi
	done
fi

echo "JAVA_HOME=$JAVA_HOME"
export PATH="$JAVA_HOME"/bin:/bin:/usr/bin
export CLASSPATH=$(ls -1 lib/* | grep jar$ | awk '{printf "%s:", $1}')
export CLASSPATH="$CLASSPATH":$scriptdir
echo "PATH=$PATH"
echo "CLASSPATH=$CLASSPATH"

FILES=$(find com -iname "*.java")

javac $FILES || exit

rm -f lib/i18n.jar
rm -f i18n.jar
jar cvf i18n.jar com
mv i18n.jar lib

java com.nantic.jasperreports.JasperServer
