package com.nantic.jasperreports;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Properties;
import java.util.Set;

public class ReportPropertiesReader {
	
	private static final String REPORT_PROPERTIES = "../report.properties";

	public Map<String,Object> readProperties(String reportDir) throws FileNotFoundException, IOException{
		Map<String, Object> propertiesMap = new HashMap<String, Object>(); 
		Properties props = loadFile(reportDir);
		Set<Entry<Object, Object>> entries = props.entrySet();
		for (Entry<Object, Object> entry : entries) {
			propertiesMap.put((String)entry.getKey(),entry.getValue());
		}
		return propertiesMap;
	}

	private Properties loadFile(String reportDir) throws FileNotFoundException, IOException{
		Properties props = new Properties();
		props.load(new FileInputStream(reportDir + REPORT_PROPERTIES));
		return props;
	}
	
//	public static void main(String[] args) throws FileNotFoundException, IOException {
//		Map<String, Object> m = new ReportPropertiesReader().readProperties();
//		Set<Entry<String, Object>> entries = m.entrySet();
//		for (Entry<String, Object> entry : entries) {
//			System.out.println(entry.getKey() + " - " + entry.getValue());
//		}
//	}
}
